package main

import (
	"discordpydebug/internal/webserver"
	"flag"
	"os"
)

func main() {
	flag.Parse()

	switch flag.Arg(0) {
	case "command":
		webserver.Setcommand(flag.Arg(1))
	default:
		webserver.Run()
	}
	os.Exit(int(0))
}
