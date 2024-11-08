package main

import (
	"bufio"
	"encoding/json"
	"fmt"
	"net"
	"os"
	"strings"
)

type Route struct {
	Origin      int     `json:"origin"`
	Destination int     `json:"destination"`
	Flow        float64 `json:"flow"`
}

type Response struct {
	Routes []Route `json:"routes"`
}

func main() {
	address := "localhost:65432"

	// Connect to the server
	client, err := net.Dial("tcp", address)
	if err != nil {
		fmt.Println("Error connecting to server:", err)
		os.Exit(1)
	}
	defer client.Close()

	// Read the instance key from user input
	reader := bufio.NewReader(os.Stdin)
	fmt.Println("Enter the instance key to retrieve from the server:")
	key, err := reader.ReadString('\n')
	if err != nil {
		fmt.Println("Error reading input:", err)
		return
	}

	// Trim any newline characters from the key
	key = strings.TrimSpace(key)

	// Send the key to the server
	_, err = client.Write([]byte(key))
	if err != nil {
		fmt.Println("Error sending data:", err)
		return
	}

	// Read the full response from the server
	response := make([]byte, 0)
	buffer := make([]byte, 1024)
	for {
		n, err := client.Read(buffer)
		if err != nil {
			if err.Error() == "EOF" {
				break
			}
			fmt.Println("Error reading response:", err)
			return
		}
		response = append(response, buffer[:n]...)
		if n < 1024 {
			break
		}
	}

	// Unmarshal the JSON response into the Response struct
	var jsonResponse struct {
		Routes [][]interface{} `json:"routes"`
	}

	err = json.Unmarshal(response, &jsonResponse)
	if err != nil {
		fmt.Println("Error unmarshalling response:", err)
		return
	}

	var res Response

	for _, route := range jsonResponse.Routes {
		if len(route) == 3 {
			origin, _ := route[0].(float64)
			destination, _ := route[1].(float64)
			flow, _ := route[2].(float64)

			res.Routes = append(res.Routes, Route{
				Origin:      int(origin),
				Destination: int(destination),
				Flow:        flow,
			})
		}
	}

	fmt.Println(res)

	for i, route := range res.Routes {
		fmt.Printf("Route %d - Origin: %d, Destination: %d, Flow: %.1f\n", i, route.Origin, route.Destination, route.Flow)
	}

}
