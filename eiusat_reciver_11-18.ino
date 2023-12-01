#include <SoftwareSerial.h>

// Set up a software serial port for communication with the H-12 radio chip
SoftwareSerial h12Serial(2, 3); // RX, TX

void setup() {
  // Set the baud rate for the software serial port
  h12Serial.begin(9600);

  // Initialize serial communication at 9600 baud rate
  Serial.begin(9600);
}

String receivedMessage = "";

// Function to perform a software reset

void loop() {
 // Check if there is data available to read from the H-12 radio chip
  while (h12Serial.available()) {
    // Read a chunk of data from the H-12 radio chip
    char chunk[32]; // Adjust the chunk size as needed
    int bytesRead = h12Serial.readBytes(chunk, sizeof(chunk));
    chunk[bytesRead] = '\0'; // Null-terminate the chunk

    // Concatenate the chunk to the received message
    receivedMessage += chunk;

    // Process the received message if it's complete
    if (receivedMessage.endsWith("}")) {
      Serial.print("Received Message: ");
      Serial.println(receivedMessage);

      // Clear the message buffer for the next message
      receivedMessage = "";
    }
  }
}
