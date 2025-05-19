package webserver

import (
	"log"
	"net/http"

	"github.com/pocketbase/pocketbase/core"
)

func InternalServerError(e *core.RequestEvent) {
	e.String(http.StatusInternalServerError, "Unable to read request body")
}

func ThrowError(err error, e *core.RequestEvent) error {
	log.Panicf("%s\n", err.Error())
	InternalServerError(e)
	return err
}
