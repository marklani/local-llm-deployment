using System;
using System.IO;
using QRCoder; // Import the QRCoder library

class Program
{
    static void Main(string[] args)
    {
        string userInput = "";

        // 1. Handle User Input: Check if arguments were passed via CLI
        if (args.Length > 0)
        {
            // Join all arguments into one string
            userInput = string.Join(" ", args);
        }
        else
        {
            // If no arguments, prompt the user manually
            Console.Write("Please enter the text or URL for the QR code: ");
            userInput = Console.ReadLine();
        }

        if (string.IsNullOrWhiteSpace(userInput))
        {
            Console.WriteLine("Error: No input provided. Exiting.");
            return;
        }

        GenerateQRCode(userInput);
    }

    static void GenerateQRCode(string text)
    {
        try
        {
            // Create the QR Generator
            using (QRCodeGenerator qrGenerator = new QRCodeGenerator())
            {
                // Create QR Data (ECCLevel.Q provides a good balance of size and error correction)
                QRCodeData qrCodeData = qrGenerator.CreateQrCode(text, QRCodeGenerator.ECCLevel.Q);

                // We use PngByteQRCode because it doesn't require System.Drawing (cross-platform friendly)
                PngByteQRCode qrCode = new PngByteQRCode(qrCodeData);

                // Get the image as a byte array (20 is the pixel size of each module)
                byte[] qrCodeAsPngByteArr = qrCode.GetGraphic(20);

                // Save the byte array as a .png file
                string fileName = "qrcode_generated.png";
                File.WriteAllBytes(fileName, qrCodeAsPngByteArr);

                Console.WriteLine($"\nSuccess! QR code generated for: '{text}'");
                Console.WriteLine($"Saved as: {Path.GetFullPath(fileName)}");
            }
        }
        catch (Exception ex)
        {
            Console.WriteLine($"An error occurred: {ex.Message}");
        }
    }
}
