package bootstrap

import (
	"context"
	"encoding/json"
	"net"
	"net/http"
	"testing"

	"github.com/voocel/agentcore"
)

func TestCreateModelFromConfig_OpenAICompatCustomProviderUsesRawBaseURL(t *testing.T) {
	seenPath := ""
	seenAuth := ""
	seenModel := ""

	handler := http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		seenPath = r.URL.Path
		seenAuth = r.Header.Get("Authorization")

		var body struct {
			Model string `json:"model"`
		}
		if err := json.NewDecoder(r.Body).Decode(&body); err != nil {
			t.Fatalf("decode request: %v", err)
		}
		seenModel = body.Model

		w.Header().Set("Content-Type", "application/json")
		_ = json.NewEncoder(w).Encode(map[string]any{
			"id":    "resp-test",
			"model": body.Model,
			"choices": []map[string]any{
				{
					"index": 0,
					"message": map[string]any{
						"role":    "assistant",
						"content": "ok",
					},
					"finish_reason": "stop",
				},
			},
			"usage": map[string]any{
				"prompt_tokens":     1,
				"completion_tokens": 1,
				"total_tokens":      2,
			},
		})
	})
	ln, err := net.Listen("tcp4", "127.0.0.1:0")
	if err != nil {
		t.Skipf("listen tcp4 unavailable in current environment: %v", err)
	}
	srv := &http.Server{Handler: handler}
	go func() { _ = srv.Serve(ln) }()
	defer func() {
		_ = srv.Shutdown(context.Background())
	}()

	model, err := createModelFromConfig(
		"doubao-test-openai-compat",
		"ep-test-123",
		ProviderConfig{
			Type:    "openai",
			APIKey:  "ark-test-key",
			BaseURL: "http://" + ln.Addr().String() + "/api/v3",
		},
		map[string]agentcore.ChatModel{},
	)
	if err != nil {
		t.Fatalf("createModelFromConfig: %v", err)
	}

	resp, err := model.Generate(context.Background(), []agentcore.Message{agentcore.UserMsg("ping")}, nil)
	if err != nil {
		t.Fatalf("Generate: %v", err)
	}
	if got := resp.Message.TextContent(); got != "ok" {
		t.Fatalf("response text = %q, want %q", got, "ok")
	}
	if seenPath != "/api/v3/chat/completions" {
		t.Fatalf("request path = %q, want %q", seenPath, "/api/v3/chat/completions")
	}
	if seenAuth != "Bearer ark-test-key" {
		t.Fatalf("auth header = %q", seenAuth)
	}
	if seenModel != "ep-test-123" {
		t.Fatalf("request model = %q, want %q", seenModel, "ep-test-123")
	}
}
