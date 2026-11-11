// FF7 Perfect Guide English patcher.
//
// Drag your .cue (or Track 1 .bin) onto the exe, or run it and pick the file.
// The patched image is written next to the original as a new .bin/.cue pair;
// your original files are never modified.
package main

import (
	"bytes"
	_ "embed"
	"fmt"
	"io"
	"os"
	"path/filepath"
	"regexp"
	"strings"
	"time"

	"ff7pg/patcher/ffpatch"
)

//go:embed patch.ffpatch
var embedded []byte

const outBase = "Final Fantasy VII International (Perfect Guide) [English]"

var fileRe = regexp.MustCompile(`(?i)^\s*FILE\s+"([^"]+)"`)

type source struct {
	files []*os.File
	sizes []int64
	desc  string
}

func (s *source) Close() {
	for _, f := range s.files {
		f.Close()
	}
}

func openSource(path string, want []uint64) (*source, error) {
	var total uint64
	for _, w := range want {
		total += w
	}
	s := &source{}
	add := func(p string) error {
		f, err := os.Open(p)
		if err != nil {
			return err
		}
		st, _ := f.Stat()
		s.files = append(s.files, f)
		s.sizes = append(s.sizes, st.Size())
		s.desc += "  " + filepath.Base(p) + "\n"
		return nil
	}
	switch strings.ToLower(filepath.Ext(path)) {
	case ".cue":
		b, err := os.ReadFile(path)
		if err != nil {
			return nil, err
		}
		for _, l := range strings.Split(string(b), "\n") {
			if m := fileRe.FindStringSubmatch(strings.TrimRight(l, "\r")); m != nil {
				if err := add(filepath.Join(filepath.Dir(path), m[1])); err != nil {
					s.Close()
					return nil, fmt.Errorf("the .cue lists %q but it can't be opened: %v", m[1], err)
				}
			}
		}
		if len(s.files) == 0 {
			return nil, fmt.Errorf("no FILE lines found in %s", filepath.Base(path))
		}
	case ".bin", ".img":
		if err := add(path); err != nil {
			return nil, err
		}
		// a Redump Track 1 dropped on its own: pick up the matching Track 2
		if uint64(s.sizes[0]) == want[0] && len(want) > 1 {
			t2 := strings.Replace(path, "(Track 1)", "(Track 2)", 1)
			if t2 != path {
				if err := add(t2); err != nil {
					s.Close()
					return nil, fmt.Errorf("found Track 1 but not %s", filepath.Base(t2))
				}
			}
		}
	case ".iso":
		return nil, fmt.Errorf(".iso files hold only 2048-byte sectors and lose the disc's video/audio data; please use a BIN/CUE dump")
	default:
		return nil, fmt.Errorf("please choose a .cue or .bin file")
	}
	var got uint64
	for _, z := range s.sizes {
		got += uint64(z)
	}
	if got != total {
		s.Close()
		return nil, fmt.Errorf("the image is %d bytes; this patch needs the Redump dump of\n"+
			"Final Fantasy VII International (Japan) (Disc 4) (Perfect Guide), %d bytes in total\n"+
			"(Track 1 + Track 2)", got, total)
	}
	return s, nil
}

func bar(label string) func(done, total int64) {
	last := time.Time{}
	return func(done, total int64) {
		if time.Since(last) < 150*time.Millisecond && done != total {
			return
		}
		last = time.Now()
		pct := float64(done) * 100 / float64(total)
		n := int(pct / 2.5)
		fmt.Printf("\r%-10s [%-40s] %5.1f%%", label, strings.Repeat("#", n), pct)
		if done == total {
			fmt.Println()
		}
	}
}

func run(path string) (string, error) {
	data := embedded
	if len(data) < 16 {
		exe, _ := os.Executable()
		matches, _ := filepath.Glob(filepath.Join(filepath.Dir(exe), "*.ffpatch"))
		if len(matches) == 0 {
			return "", fmt.Errorf("no patch data found")
		}
		var err error
		if data, err = os.ReadFile(matches[0]); err != nil {
			return "", err
		}
	}
	h, ops, err := ffpatch.ReadHeader(bytes.NewReader(data))
	if err != nil {
		return "", err
	}
	fmt.Println(h.Title)
	fmt.Println()
	src, err := openSource(path, h.SrcParts)
	if err != nil {
		return "", err
	}
	defer src.Close()
	fmt.Print("Source:\n" + src.desc + "\n")
	parts := make([]io.ReaderAt, len(src.files))
	for i, f := range src.files {
		parts[i] = f
	}
	m := ffpatch.NewMulti(parts, src.sizes)
	sum, err := ffpatch.SourceMD5(m, bar("Checking"))
	if err != nil {
		return "", err
	}
	if sum != h.SrcMD5 {
		return "", fmt.Errorf("this doesn't look like an unmodified Redump image of the disc\n"+
			"(MD5 %x, expected %x)", sum, h.SrcMD5)
	}
	dir := filepath.Dir(path)
	outBin := filepath.Join(dir, outBase+".bin")
	outCue := filepath.Join(dir, outBase+".cue")
	tmp := outBin + ".part"
	f, err := os.Create(tmp)
	if err != nil {
		return "", err
	}
	err = ffpatch.Apply(h, ops, m, f, bar("Patching"))
	f.Close()
	if err != nil {
		os.Remove(tmp)
		return "", err
	}
	os.Remove(outBin)
	if err := os.Rename(tmp, outBin); err != nil {
		return "", err
	}
	cue := fmt.Sprintf(h.CueTemplate, filepath.Base(outBin))
	cue = strings.ReplaceAll(cue, "\n", "\r\n")
	if err := os.WriteFile(outCue, []byte(cue), 0644); err != nil {
		return "", err
	}
	return outCue, nil
}

func main() {
	setTitle("FF7 Perfect Guide - English patch")
	path := ""
	if len(os.Args) > 1 {
		path = os.Args[1]
	} else {
		fmt.Println("Choose your disc image (.cue, or the Track 1 .bin)...")
		path = pickFile()
		if path == "" {
			return
		}
	}
	out, err := run(path)
	if err != nil {
		fmt.Println("\nERROR:", err)
		message("FF7 Perfect Guide - English patch", "Patching failed:\n\n"+err.Error(), true)
		return
	}
	fmt.Println("\nDone! Created:\n  " + out)
	message("FF7 Perfect Guide - English patch", "Done! Load this file in your emulator:\n\n"+out, false)
}
