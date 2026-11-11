//go:build windows

package main

import (
	"syscall"
	"unsafe"
)

var (
	comdlg32         = syscall.NewLazyDLL("comdlg32.dll")
	user32           = syscall.NewLazyDLL("user32.dll")
	kernel32         = syscall.NewLazyDLL("kernel32.dll")
	pGetOpenFileName = comdlg32.NewProc("GetOpenFileNameW")
	pMessageBox      = user32.NewProc("MessageBoxW")
	pSetConsoleTitle = kernel32.NewProc("SetConsoleTitleW")
)

type openFileName struct {
	lStructSize       uint32
	hwndOwner         uintptr
	hInstance         uintptr
	lpstrFilter       *uint16
	lpstrCustomFilter *uint16
	nMaxCustFilter    uint32
	nFilterIndex      uint32
	lpstrFile         *uint16
	nMaxFile          uint32
	lpstrFileTitle    *uint16
	nMaxFileTitle     uint32
	lpstrInitialDir   *uint16
	lpstrTitle        *uint16
	flags             uint32
	nFileOffset       uint16
	nFileExtension    uint16
	lpstrDefExt       *uint16
	lCustData         uintptr
	lpfnHook          uintptr
	lpTemplateName    *uint16
	pvReserved        uintptr
	dwReserved        uint32
	flagsEx           uint32
}

func utf16z(s string) []uint16 {
	u, _ := syscall.UTF16FromString(s)
	return u
}

func pickFile() string {
	buf := make([]uint16, 32768)
	// filter: pairs separated by NUL, terminated by double NUL
	filter := utf16z("Disc image (*.cue;*.bin)\x00*.cue;*.bin\x00All files\x00*.*\x00")
	title := utf16z("Choose the FF7 Perfect Guide disc image (.cue)")
	ofn := openFileName{
		lpstrFilter: &filter[0],
		lpstrFile:   &buf[0],
		nMaxFile:    uint32(len(buf)),
		lpstrTitle:  &title[0],
		flags:       0x00001000 | 0x00000800 | 0x00080000, // FILEMUSTEXIST | PATHMUSTEXIST | EXPLORER
	}
	ofn.lStructSize = uint32(unsafe.Sizeof(ofn))
	r, _, _ := pGetOpenFileName.Call(uintptr(unsafe.Pointer(&ofn)))
	if r == 0 {
		return ""
	}
	return syscall.UTF16ToString(buf)
}

func message(title, text string, isErr bool) {
	t := utf16z(title)
	m := utf16z(text)
	flags := uintptr(0x40) // MB_ICONINFORMATION
	if isErr {
		flags = 0x10 // MB_ICONERROR
	}
	pMessageBox.Call(0, uintptr(unsafe.Pointer(&m[0])), uintptr(unsafe.Pointer(&t[0])), flags)
}

func setTitle(s string) {
	t := utf16z(s)
	pSetConsoleTitle.Call(uintptr(unsafe.Pointer(&t[0])))
}
