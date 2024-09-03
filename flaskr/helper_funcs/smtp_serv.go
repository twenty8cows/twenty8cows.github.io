package main

import (
	"bufio"
	"log"
	"net"
	"net/http"
	"net/url"
	"os"
	"strings"

	"github.com/joho/godotenv"
)

func init() {
    // Load the .env file
    err := godotenv.Load()
    if err != nil {
        log.Fatal("Error loading .env file")
    }
}

func handleClient(conn net.Conn) {
    defer conn.Close()

    reader := bufio.NewReader(conn)
    writer := bufio.NewWriter(conn)

    // Send initial SMTP server greeting
    writer.WriteString("220 Welcome to Go SMTP Server\r\n")
    writer.Flush()

    var mailFrom string
    var rcptTo string
    var messageData strings.Builder

    for {
        line, err := reader.ReadString('\n')
        if err != nil {
            log.Println("Error reading line:", err)
            return
        }

        line = strings.TrimSpace(line)
        log.Println("Received:", line)

        switch {
        case strings.HasPrefix(strings.ToUpper(line), "EHLO"):
            writer.WriteString("250-Hello\r\n")
            writer.WriteString("250-PIPELINING\r\n")
            writer.WriteString("250 AUTH\r\n")
            writer.WriteString("250 OK\r\n")

        case strings.HasPrefix(strings.ToUpper(line), "HELO"):
            writer.WriteString("250 Hello\r\n")

        case strings.HasPrefix(strings.ToUpper(line), "MAIL FROM:"):
            mailFrom = line[10:]  // Extract email address
            writer.WriteString("250 OK\r\n")

        case strings.HasPrefix(strings.ToUpper(line), "RCPT TO:"):
            rcptTo = line[8:]  // Extract recipient address
            writer.WriteString("250 OK\r\n")

        case strings.HasPrefix(strings.ToUpper(line), "DATA"):
            writer.WriteString("354 End data with <CR><LF>.<CR><LF>\r\n")
            writer.Flush()

            for {
                dataLine, err := reader.ReadString('\n')
                if err != nil {
                    if err.Error() == "EOF" {
                        log.Println("Error: Unexpected EOF received while reading data")
                        return
                    }
                    log.Println("Error reading data:", err)
                    return
                }

                dataLine = strings.TrimRight(dataLine, "\r\n")
                if dataLine == "." {
                    break
                }

                messageData.WriteString(dataLine + "\r\n")
            }

            log.Println("Data received:", messageData.String())
            writer.WriteString("250 OK\r\n")
            writer.Flush()

            // Now send the email using Mailgun's API
            sendEmailWithMailgun(mailFrom, rcptTo, "Forwarded Email", messageData.String())

        case strings.HasPrefix(strings.ToUpper(line), "QUIT"):
            writer.WriteString("221 Bye\r\n")
            writer.Flush()
            return

        default:
            writer.WriteString("500 Unrecognized command\r\n")
        }

        writer.Flush()
    }
}

func sendEmailWithMailgun(from string, to string, subject string, body string) {
    domain := os.Getenv("MAILGUN_DOMAIN")
    apiKey := os.Getenv("MAILGUN_API_KEY")

    apiURL := "https://api.mailgun.net/v3/" + domain + "/messages"
    data := url.Values{}
    data.Set("from", from)
    data.Set("to", to)
    data.Set("subject", subject)
    data.Set("text", body)

    req, err := http.NewRequest("POST", apiURL, strings.NewReader(data.Encode()))
    if err != nil {
        log.Println("Failed to create request:", err)
        return
    }
    req.SetBasicAuth("api", apiKey)
    req.Header.Add("Content-Type", "application/x-www-form-urlencoded")

    client := &http.Client{}
    resp, err := client.Do(req)
    if err != nil {
        log.Println("Failed to send email:", err)
        return
    }
    defer resp.Body.Close()

    if resp.StatusCode == 200 {
        log.Println("Email sent successfully to", to)
    } else {
        log.Println("Failed to send email, status code:", resp.StatusCode)
    }
}

func main() {
    listener, err := net.Listen("tcp", ":1025")
    if err != nil {
        log.Fatal("Failed to listen on port 1025:", err)
    }
    defer listener.Close()

    log.Println("SMTP server listening on port 1025")

    for {
        conn, err := listener.Accept()
        if err != nil {
            log.Println("Failed to accept connection:", err)
            continue
        }
        go handleClient(conn)
    }
}
