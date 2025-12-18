package main

import (
	"context"
	"encoding/json"
	"flag"
	"fmt"
	"log"
	"net/http"
	"os"
	"os/signal"
	"path/filepath"
	"syscall"
	"time"

	"github.com/altskydev/altsky/backend/statscalc/internal/data"
	"github.com/altskydev/altsky/backend/statscalc/internal/model"
	"github.com/altskydev/altsky/backend/statscalc/internal/service/calculator"
)

func main() {
	var (
		dataDir  = flag.String("data", "./data", "path to stats definition directory")
		addr     = flag.String("addr", ":8082", "HTTP listen address")
		poll     = flag.Duration("poll", 2*time.Second, "data directory polling interval")
	)
	flag.Parse()

	statsDir := filepath.Join(*dataDir, "stats")
	loader, err := data.NewLoader(statsDir, *poll)
	if err != nil {
		log.Fatalf("failed to init loader: %v", err)
	}

	ctx, cancel := context.WithCancel(context.Background())
	defer cancel()
	loader.StartWatch(ctx)

	calc := calculator.New(loader)
	server := &http.Server{
		Addr:    *addr,
		Handler: routes(calc),
	}

	go func() {
		log.Printf("statscalc listening on %s", *addr)
		if err := server.ListenAndServe(); err != nil && err != http.ErrServerClosed {
			log.Fatalf("http server: %v", err)
		}
	}()

	waitForSignal()
	log.Println("shutting down statscalc...")
	shutdownCtx, shutdownCancel := context.WithTimeout(context.Background(), 5*time.Second)
	defer shutdownCancel()
	if err := server.Shutdown(shutdownCtx); err != nil {
		log.Printf("server shutdown error: %v", err)
	}
}

func routes(calc *calculator.Calculator) http.Handler {
	mux := http.NewServeMux()
	mux.HandleFunc("/health", func(w http.ResponseWriter, r *http.Request) {
		w.WriteHeader(http.StatusOK)
		w.Write([]byte("ok"))
	})
	mux.HandleFunc("/stats", func(w http.ResponseWriter, r *http.Request) {
		if r.Method != http.MethodPost {
			http.Error(w, "method not allowed", http.StatusMethodNotAllowed)
			return
		}
		defer r.Body.Close()

		var profile model.PlayerProfile
		if err := json.NewDecoder(r.Body).Decode(&profile); err != nil {
			http.Error(w, fmt.Sprintf("invalid payload: %v", err), http.StatusBadRequest)
			return
		}

		stats := calc.Calculate(profile)
		w.Header().Set("Content-Type", "application/json")
		json.NewEncoder(w).Encode(map[string]any{
			"stats": stats,
		})
	})
	return mux
}

func waitForSignal() {
	ch := make(chan os.Signal, 1)
	signal.Notify(ch, syscall.SIGINT, syscall.SIGTERM)
	<-ch
}
