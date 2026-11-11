// Package ffpatch implements a small sector-aware CD image patch format.
//
// The target image is rebuilt sector by sector (2352 bytes) from the user's own
// source image. Sectors that exist in the source are copied (for Mode 2 data
// sectors only bytes 16..2351 are copied and the sync/address header is
// regenerated, so moved files cost nothing). Changed sectors are stored as an
// XOR against a source sector when that is cheaper, or as literal data.
// The op stream is deflate-compressed.
package ffpatch

import (
	"bufio"
	"bytes"
	"compress/flate"
	"crypto/md5"
	"encoding/binary"
	"errors"
	"fmt"
	"io"
)

const (
	Sector  = 2352
	Magic   = "FF7PGP1\x00"
	opRaw   = 0 // copy raw sectors from source
	opData  = 1 // copy bytes 16.. from source, regenerate header
	opXor   = 2 // regenerate header, bytes 16.. = source[16:] XOR literal
	opLit   = 3 // literal sectors
	opEnd   = 0xFF
	DataLen = Sector - 16
)

// Header describes what the patch expects and produces.
type Header struct {
	SrcParts    []uint64 // sizes of the source parts (e.g. Track 1, Track 2)
	SrcMD5      [16]byte // md5 of the concatenated source
	TgtSize     uint64
	TgtMD5      [16]byte
	TgtDataSecs uint32 // target sectors [0,TgtDataSecs) are Mode 2 data sectors
	Title       string
	CueTemplate string // %s = output .bin file name
}

// ReaderAtSize is a random-access source image.
type ReaderAtSize interface {
	io.ReaderAt
	Size() int64
}

// MultiReaderAt concatenates several ReaderAts (split-track images).
type MultiReaderAt struct {
	parts []io.ReaderAt
	sizes []int64
	total int64
}

func NewMulti(parts []io.ReaderAt, sizes []int64) *MultiReaderAt {
	m := &MultiReaderAt{parts: parts, sizes: sizes}
	for _, s := range sizes {
		m.total += s
	}
	return m
}
func (m *MultiReaderAt) Size() int64 { return m.total }
func (m *MultiReaderAt) ReadAt(p []byte, off int64) (int, error) {
	n := 0
	for i, part := range m.parts {
		if off >= m.sizes[i] {
			off -= m.sizes[i]
			continue
		}
		for len(p) > 0 && off < m.sizes[i] {
			want := int64(len(p))
			if off+want > m.sizes[i] {
				want = m.sizes[i] - off
			}
			k, err := part.ReadAt(p[:want], off)
			n += k
			p = p[k:]
			off += int64(k)
			if err != nil && !(errors.Is(err, io.EOF) && k == int(want)) {
				return n, err
			}
		}
		off = 0
		if len(p) == 0 {
			return n, nil
		}
	}
	if len(p) > 0 {
		return n, io.EOF
	}
	return n, nil
}

func bcd(v int) byte { return byte((v/10)<<4 | v%10) }

// SectorHeader writes the 16-byte sync+address+mode header for absolute sector lba (0-based in the image).
func SectorHeader(dst []byte, lba int) {
	dst[0] = 0
	for i := 1; i < 11; i++ {
		dst[i] = 0xFF
	}
	dst[11] = 0
	a := lba + 150
	dst[12] = bcd(a / 4500)
	dst[13] = bcd(a / 75 % 60)
	dst[14] = bcd(a % 75)
	dst[15] = 2
}

func putUvarint(w io.Writer, v uint64) error {
	var b [binary.MaxVarintLen64]byte
	_, err := w.Write(b[:binary.PutUvarint(b[:], v)])
	return err
}

func writeString(w io.Writer, s string) error {
	if err := putUvarint(w, uint64(len(s))); err != nil {
		return err
	}
	_, err := io.WriteString(w, s)
	return err
}

func readString(r *bufio.Reader) (string, error) {
	n, err := binary.ReadUvarint(r)
	if err != nil {
		return "", err
	}
	if n > 1<<20 {
		return "", errors.New("bad string length")
	}
	b := make([]byte, n)
	_, err = io.ReadFull(r, b)
	return string(b), err
}

func (h *Header) write(w io.Writer) error {
	io.WriteString(w, Magic)
	putUvarint(w, uint64(len(h.SrcParts)))
	for _, s := range h.SrcParts {
		putUvarint(w, s)
	}
	w.Write(h.SrcMD5[:])
	putUvarint(w, h.TgtSize)
	w.Write(h.TgtMD5[:])
	putUvarint(w, uint64(h.TgtDataSecs))
	writeString(w, h.Title)
	return writeString(w, h.CueTemplate)
}

// ReadHeader parses the patch header and returns a reader positioned at the op stream.
func ReadHeader(r io.Reader) (*Header, *bufio.Reader, error) {
	br := bufio.NewReader(r)
	m := make([]byte, len(Magic))
	if _, err := io.ReadFull(br, m); err != nil || string(m) != Magic {
		return nil, nil, errors.New("not an FF7PG patch")
	}
	h := &Header{}
	n, err := binary.ReadUvarint(br)
	if err != nil || n > 16 {
		return nil, nil, errors.New("bad header")
	}
	for i := uint64(0); i < n; i++ {
		s, err := binary.ReadUvarint(br)
		if err != nil {
			return nil, nil, err
		}
		h.SrcParts = append(h.SrcParts, s)
	}
	io.ReadFull(br, h.SrcMD5[:])
	h.TgtSize, _ = binary.ReadUvarint(br)
	io.ReadFull(br, h.TgtMD5[:])
	ds, _ := binary.ReadUvarint(br)
	h.TgtDataSecs = uint32(ds)
	if h.Title, err = readString(br); err != nil {
		return nil, nil, err
	}
	if h.CueTemplate, err = readString(br); err != nil {
		return nil, nil, err
	}
	return h, br, nil
}

// ---------------------------------------------------------------- encoder

type opw struct {
	w            *bufio.Writer
	op           int
	src, count   uint64
	lit          bytes.Buffer
	nRaw, nData  int
	nXor, nLit   int
}

func (o *opw) flush() error {
	if o.count == 0 {
		return nil
	}
	o.w.WriteByte(byte(o.op))
	putUvarint(o.w, o.count)
	if o.op != opLit {
		putUvarint(o.w, o.src)
	}
	if o.lit.Len() > 0 {
		o.w.Write(o.lit.Bytes())
		o.lit.Reset()
	}
	o.count = 0
	return nil
}

func (o *opw) add(op int, src uint64, lit []byte) {
	contiguous := o.count > 0 && o.op == op && (op == opLit || o.src+o.count == src)
	if !contiguous || o.count >= 1<<20 {
		o.flush()
		o.op, o.src = op, src
	}
	o.count++
	o.lit.Write(lit)
	switch op {
	case opRaw:
		o.nRaw++
	case opData:
		o.nData++
	case opXor:
		o.nXor++
	default:
		o.nLit++
	}
}

type hash16 [16]byte

// Encode writes a patch turning src into tgt. srcDataSecs: source sectors [0,n) are Mode 2 data.
func Encode(out io.Writer, src ReaderAtSize, srcParts []uint64, srcDataSecs int, tgt ReaderAtSize, tgtDataSecs int, title, cue string, logf func(string, ...any)) error {
	ns := int(src.Size() / Sector)
	nt := int(tgt.Size() / Sector)
	if int64(nt)*Sector != tgt.Size() || int64(ns)*Sector != src.Size() {
		return errors.New("image sizes must be whole 2352-byte sectors")
	}
	h := &Header{SrcParts: srcParts, TgtSize: uint64(tgt.Size()), TgtDataSecs: uint32(tgtDataSecs), Title: title, CueTemplate: cue}
	logf("indexing source (%d sectors)...", ns)
	byData := make(map[hash16]uint32, srcDataSecs)
	byRaw := make(map[hash16]uint32, ns)
	smd5 := md5.New()
	buf := make([]byte, Sector)
	for i := 0; i < ns; i++ {
		if _, err := src.ReadAt(buf, int64(i)*Sector); err != nil {
			return err
		}
		smd5.Write(buf)
		hr := hash16(md5.Sum(buf))
		if _, ok := byRaw[hr]; !ok {
			byRaw[hr] = uint32(i)
		}
		if i < srcDataSecs {
			hd := hash16(md5.Sum(buf[16:]))
			if _, ok := byData[hd]; !ok {
				byData[hd] = uint32(i)
			}
		}
	}
	copy(h.SrcMD5[:], smd5.Sum(nil))

	// first pass: target md5 (header needs it)
	tmd5 := md5.New()
	for i := 0; i < nt; i++ {
		tgt.ReadAt(buf, int64(i)*Sector)
		tmd5.Write(buf)
	}
	copy(h.TgtMD5[:], tmd5.Sum(nil))

	bw := bufio.NewWriterSize(out, 1<<20)
	if err := h.write(bw); err != nil {
		return err
	}
	fw, _ := flate.NewWriter(bw, flate.BestCompression)
	o := &opw{w: bufio.NewWriterSize(fw, 1<<20)}
	sb := make([]byte, Sector)
	hdr := make([]byte, 16)
	x := make([]byte, DataLen)
	next := uint64(0) // predicted source sector for xor
	logf("encoding target (%d sectors)...", nt)
	for i := 0; i < nt; i++ {
		tgt.ReadAt(buf, int64(i)*Sector)
		isData := i < tgtDataSecs
		if isData {
			SectorHeader(hdr, i)
			if !bytes.Equal(hdr, buf[:16]) {
				isData = false // unexpected header: store raw
			}
		}
		if isData {
			if s, ok := byData[hash16(md5.Sum(buf[16:]))]; ok {
				// prefer the predicted sector when it matches too (keeps runs long)
				if next < uint64(srcDataSecs) {
					src.ReadAt(sb, int64(next)*Sector)
					if bytes.Equal(sb[16:], buf[16:]) {
						s = uint32(next)
					}
				}
				o.add(opData, uint64(s), nil)
				next = uint64(s) + 1
				continue
			}
		} else if s, ok := byRaw[hash16(md5.Sum(buf))]; ok {
			if next < uint64(ns) {
				src.ReadAt(sb, int64(next)*Sector)
				if bytes.Equal(sb, buf) {
					s = uint32(next)
				}
			}
			o.add(opRaw, uint64(s), nil)
			next = uint64(s) + 1
			continue
		}
		if isData && next < uint64(srcDataSecs) {
			src.ReadAt(sb, int64(next)*Sector)
			diff := 0
			for k := 0; k < DataLen; k++ {
				x[k] = sb[16+k] ^ buf[16+k]
				if x[k] != 0 {
					diff++
				}
			}
			if diff < DataLen/2 {
				o.add(opXor, next, x)
				next++
				continue
			}
		}
		o.add(opLit, 0, buf)
		next++
	}
	o.flush()
	o.w.WriteByte(opEnd)
	o.w.Flush()
	fw.Close()
	logf("sectors: copied %d raw + %d data, %d xor, %d literal", o.nRaw, o.nData, o.nXor, o.nLit)
	return bw.Flush()
}

// ---------------------------------------------------------------- decoder

// SourceMD5 hashes the whole source (call before Apply to give a friendly error).
func SourceMD5(src ReaderAtSize, progress func(done, total int64)) ([16]byte, error) {
	h := md5.New()
	buf := make([]byte, 1<<20)
	var off int64
	for off < src.Size() {
		n := int64(len(buf))
		if off+n > src.Size() {
			n = src.Size() - off
		}
		if _, err := src.ReadAt(buf[:n], off); err != nil {
			return [16]byte{}, err
		}
		h.Write(buf[:n])
		off += n
		if progress != nil {
			progress(off, src.Size())
		}
	}
	var s [16]byte
	copy(s[:], h.Sum(nil))
	return s, nil
}

// Apply rebuilds the target image into out. It verifies the target md5.
func Apply(h *Header, ops *bufio.Reader, src ReaderAtSize, out io.Writer, progress func(done, total int64)) error {
	fr := bufio.NewReaderSize(flate.NewReader(ops), 1<<20)
	md := md5.New()
	w := bufio.NewWriterSize(io.MultiWriter(out, md), 1<<20)
	buf := make([]byte, Sector)
	x := make([]byte, DataLen)
	total := int64(h.TgtSize)
	var lba int64
	emit := func() {
		w.Write(buf)
		lba++
		if progress != nil && lba%512 == 0 {
			progress(lba*Sector, total)
		}
	}
	for {
		op, err := fr.ReadByte()
		if err != nil {
			return fmt.Errorf("patch data truncated: %w", err)
		}
		if op == opEnd {
			break
		}
		count, err := binary.ReadUvarint(fr)
		if err != nil {
			return err
		}
		var s uint64
		if op != opLit {
			if s, err = binary.ReadUvarint(fr); err != nil {
				return err
			}
		}
		for k := uint64(0); k < count; k++ {
			switch op {
			case opRaw:
				if _, err := src.ReadAt(buf, int64(s+k)*Sector); err != nil {
					return err
				}
			case opData, opXor:
				if _, err := src.ReadAt(buf, int64(s+k)*Sector); err != nil {
					return err
				}
				SectorHeader(buf, int(lba))
				if op == opXor {
					if _, err := io.ReadFull(fr, x); err != nil {
						return err
					}
					for i := range x {
						buf[16+i] ^= x[i]
					}
				}
			case opLit:
				if _, err := io.ReadFull(fr, buf); err != nil {
					return err
				}
			default:
				return fmt.Errorf("bad op %d", op)
			}
			emit()
		}
	}
	if err := w.Flush(); err != nil {
		return err
	}
	if lba*Sector != total {
		return fmt.Errorf("output size %d, expected %d", lba*Sector, total)
	}
	var got [16]byte
	copy(got[:], md.Sum(nil))
	if got != h.TgtMD5 {
		return errors.New("output checksum mismatch")
	}
	if progress != nil {
		progress(total, total)
	}
	return nil
}
