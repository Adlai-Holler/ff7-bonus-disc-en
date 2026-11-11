// mkpatch builds the release patch.
//
//	mkpatch <original .cue> <built .bin> <built .cue> <out.ffpatch> [title]
//
// The original cue lists the Redump Track 1/Track 2 bins; the built cue is the
// one mkpsxiso wrote (used to find where the audio track starts and as the
// template for the cue the patcher writes).
package main

import (
	"fmt"
	"io"
	"os"
	"path/filepath"
	"regexp"
	"strconv"
	"strings"

	"ff7pg/patcher/ffpatch"
)

func die(f string, a ...any) { fmt.Fprintf(os.Stderr, f+"\n", a...); os.Exit(1) }

var fileRe = regexp.MustCompile(`(?i)^\s*FILE\s+"([^"]+)"`)
var idxRe = regexp.MustCompile(`(?i)^\s*INDEX\s+(\d+)\s+(\d+):(\d+):(\d+)`)
var trkRe = regexp.MustCompile(`(?i)^\s*TRACK\s+(\d+)\s+(\S+)`)

func cueFiles(cue string) []string {
	b, err := os.ReadFile(cue)
	if err != nil {
		die("%v", err)
	}
	var out []string
	for _, l := range strings.Split(string(b), "\n") {
		if m := fileRe.FindStringSubmatch(l); m != nil {
			out = append(out, filepath.Join(filepath.Dir(cue), m[1]))
		}
	}
	return out
}

// first sector of the first AUDIO track's INDEX 00 (or 01) in a single-file cue
func audioStart(cue string) int {
	b, _ := os.ReadFile(cue)
	audio := false
	for _, l := range strings.Split(string(b), "\n") {
		if m := trkRe.FindStringSubmatch(l); m != nil {
			audio = strings.EqualFold(m[2], "AUDIO")
		}
		if m := idxRe.FindStringSubmatch(l); m != nil && audio {
			mm, _ := strconv.Atoi(m[2])
			ss, _ := strconv.Atoi(m[3])
			ff, _ := strconv.Atoi(m[4])
			return (mm*60+ss)*75 + ff
		}
	}
	return -1
}

func open(p string) (*os.File, int64) {
	f, err := os.Open(p)
	if err != nil {
		die("%v", err)
	}
	st, _ := f.Stat()
	return f, st.Size()
}

func main() {
	if len(os.Args) < 5 {
		die("usage: mkpatch <original.cue> <built.bin> <built.cue> <out.ffpatch> [title]")
	}
	title := "Final Fantasy VII International Perfect Guide - English"
	if len(os.Args) > 5 {
		title = os.Args[5]
	}
	var parts []io.ReaderAt
	var sizes []int64
	var usizes []uint64
	for _, p := range cueFiles(os.Args[1]) {
		f, s := open(p)
		parts = append(parts, f)
		sizes = append(sizes, s)
		usizes = append(usizes, uint64(s))
		fmt.Printf("source part %s (%d bytes)\n", filepath.Base(p), s)
	}
	if len(parts) == 0 {
		die("no FILE entries in %s", os.Args[1])
	}
	src := ffpatch.NewMulti(parts, sizes)
	srcData := int(sizes[0] / ffpatch.Sector) // Track 1 = data
	tf, ts := open(os.Args[2])
	tgt := ffpatch.NewMulti([]io.ReaderAt{tf}, []int64{ts})
	tgtData := audioStart(os.Args[3])
	if tgtData < 0 {
		die("no AUDIO track in %s", os.Args[3])
	}
	// cue template: same as the built cue with the file name replaced
	cb, _ := os.ReadFile(os.Args[3])
	cue := fileRe.ReplaceAllString(strings.ReplaceAll(string(cb), "%", "%%"), `FILE "%s"`)
	cue = strings.ReplaceAll(cue, "\r\n", "\n")
	out, err := os.Create(os.Args[4])
	if err != nil {
		die("%v", err)
	}
	err = ffpatch.Encode(out, src, usizes, srcData, tgt, tgtData, title, cue, func(f string, a ...any) { fmt.Printf(f+"\n", a...) })
	if err != nil {
		die("encode: %v", err)
	}
	out.Close()
	st, _ := os.Stat(os.Args[4])
	fmt.Printf("wrote %s (%d bytes)\n", os.Args[4], st.Size())
}
