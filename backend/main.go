package main

import (
	"bufio"
	"fmt"
	"net"
	"os"
	"strings"
)

func main() {
	serverAddress := "localhost:65432"

	conn, err := net.Dial("tcp", serverAddress)
	if err != nil {
		fmt.Println("Error connecting to server:", err)
		return
	}
	defer conn.Close()

	reader := bufio.NewReader(os.Stdin)

	fmt.Println("Enter the key to retrieve from Redis:")

	key, err := reader.ReadString('\n')
	if err != nil {
		fmt.Println("Error reading input:", err)
		return
	}

	// Trim any newline characters from the key
	key = strings.TrimSpace(key)

	// Send the key to the server
	_, err = conn.Write([]byte(key))
	if err != nil {
		fmt.Println("Error sending data:", err)
		return
	}

	// Receive response from the server
	buffer := make([]byte, 1024)
	n, err := conn.Read(buffer)
	if err != nil {
		fmt.Println("Error reading response:", err)
		return
	}

	// Print the server response
	fmt.Println("Server response:", string(buffer[:n]))
}
