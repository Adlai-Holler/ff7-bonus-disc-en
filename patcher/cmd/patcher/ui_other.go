//go:build !windows

package main

import (
	"bufio"
	"fmt"
	"os"
	"strings"
)

func pickFile() string {
	fmt.Print("Path to .cue or .bin: ")
	s, _ := bufio.NewReader(os.Stdin).ReadString('\n')
	return strings.Trim(strings.TrimSpace(s), `"`)
}

func message(title, text string, isErr bool) {}
func setTitle(s string)                       {}
