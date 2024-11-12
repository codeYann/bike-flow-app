package server

import (
	"fmt"
	"log"
	"net/http"
	"os"
	"strconv"
	"time"

	"github.com/joho/godotenv"
)

type Server struct {
	port int
}

func NewServer() *http.Server {
	err := godotenv.Load()
	if err != nil {
		log.Fatalf("Error loading .env file")
		panic(err)
	}

	port, _ := strconv.Atoi(os.Getenv("PORT"))

	newServer := &Server{
		port: port,
	}

	srv := &http.Server{
		Addr:         fmt.Sprintf(":%d", newServer.port),
		Handler:      nil,
		IdleTimeout:  time.Minute,
		ReadTimeout:  time.Second * 10,
		WriteTimeout: time.Second * 30,
	}

	return srv
}
