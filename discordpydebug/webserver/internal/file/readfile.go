package file

import (
	"fmt"
	"os"
)

func ReadFile() []byte {
	data, err := os.ReadFile("./payload.txt")
	if err != nil {
		fmt.Printf("%s", err.Error())
		return []byte("")
	}
	return data
}
