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

type Coordinates struct {
	Latitude  float64 `json:"latitude"`
	Longitude float64 `json:"longitude"`
}

type Response struct {
	Routes         []Route       `json:"routes"`
	Coordinates    []Coordinates `json:"coordinates"`
	AvailableBikes []int         `json:"availableBikes"`
	FreeSlots      []int         `json:"freeSlots"`
}

func connectToServer(address string) (net.Conn, error) {
	client, err := net.Dial("tcp", address)
	if err != nil {
		return nil, fmt.Errorf("error connecting to server: %w", err)
	}
	return client, nil
}

func readUserInput(prompt string) (string, error) {
	reader := bufio.NewReader(os.Stdin)
	fmt.Println(prompt)
	key, err := reader.ReadString('\n')
	if err != nil {
		return "", fmt.Errorf("error reading input: %w", err)
	}
	return strings.TrimSpace(key), nil
}

func sendKeyToServer(client net.Conn, key string) error {
	_, err := client.Write([]byte(key))
	if err != nil {
		return fmt.Errorf("error sending data: %w", err)
	}
	return nil
}

func readServerResponse(client net.Conn) ([]byte, error) {
	var response []byte
	buffer := make([]byte, 1024)
	for {
		n, err := client.Read(buffer)
		if err != nil {
			if err.Error() == "EOF" {
				break
			}
			return nil, fmt.Errorf("error reading response: %w", err)
		}
		response = append(response, buffer[:n]...)
		if n < 1024 {
			break
		}
	}
	return response, nil
}

func parseResponse(response []byte) (Response, error) {
	var jsonResponse struct {
		Routes         [][]interface{} `json:"routes"`
		Coordinates    [][]interface{} `json:"coordinates"`
		AvailableBikes []interface{}   `json:"availableBikes"`
		FreeSlots      []interface{}   `json:"freeSlots"`
	}

	err := json.Unmarshal(response, &jsonResponse)
	if err != nil {
		return Response{}, fmt.Errorf("error unmarshalling response: %w", err)
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

	for _, coord := range jsonResponse.Coordinates {
		if len(coord) == 2 {
			latitude, _ := coord[0].(float64)
			longitude, _ := coord[1].(float64)
			res.Coordinates = append(res.Coordinates, Coordinates{
				Latitude:  latitude,
				Longitude: longitude,
			})
		}
	}

	for _, bike := range jsonResponse.AvailableBikes {
		if bikeCount, ok := bike.(float64); ok {
			res.AvailableBikes = append(res.AvailableBikes, int(bikeCount))
		}
	}

	for _, slot := range jsonResponse.FreeSlots {
		if slotCount, ok := slot.(float64); ok {
			res.FreeSlots = append(res.FreeSlots, int(slotCount))
		}
	}

	return res, nil
}

func main() {
	address := "localhost:65432"

	client, err := connectToServer(address)
	if err != nil {
		fmt.Println(err)
		os.Exit(1)
	}
	defer client.Close()

	key, err := readUserInput("Enter the instance key to retrieve from the server:")
	if err != nil {
		fmt.Println(err)
		return
	}

	if err := sendKeyToServer(client, key); err != nil {
		fmt.Println(err)
		return
	}

	response, err := readServerResponse(client)
	if err != nil {
		fmt.Println(err)
		return
	}

	res, err := parseResponse(response)
	if err != nil {
		fmt.Println(err)
		return
	}

	fmt.Println(res)
}
