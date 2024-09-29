using System;
using System.CodeDom.Compiler;
using System.CodeDom;
using System.Collections;
using System.Collections.Generic;
using System.IO;
using System.IO.Ports;
using System.Linq;
using System.Runtime.Remoting.Messaging;
using System.Text;
using System.Threading.Tasks;
using System.Windows.Forms;

namespace ASCOM.LiamDaviesSprinterDFL.Switch
{
    public class CommandCallback
    {
        public delegate void ResponseReceived(string response);

        public string command;
        public ResponseReceived response;

        public CommandCallback(string command, ResponseReceived response = null)
        {
            this.command = command;
            this.response = response;
        }
    }

    internal static class SerialDriver
    {
        static SerialPort serialPort;

        static string data_buffer = "";

        // A queue of recently requested Command Callbacks.
        // Will be sent and received one at a time.
        public static Queue<CommandCallback> command_queue = new Queue<CommandCallback>();

        public static void OpenSerialPort()
        {
            if(serialPort != null && serialPort.IsOpen)
            {
                return;
            }
            serialPort = new SerialPort();
            serialPort.PortName = SwitchHardware.comPort;
            serialPort.BaudRate = SwitchHardware.baudRate;
            serialPort.ReadTimeout = 3000;
            serialPort.WriteTimeout = 3000;
            serialPort.NewLine = "\r\n";

            serialPort.DataReceived += new SerialDataReceivedEventHandler(DataReceivedHandler);
            // Attempt open.
            serialPort.Open();
        }

        public static void CloseSerialPort()
        {
            command_queue.Clear();
            serialPort.Close();
        }
        public static void ClearCommandQueue(bool respondEmpty = true)
        {
            if(respondEmpty)
            {
                // Respond to all remaining commands in the queue.
                while(command_queue.Count > 0)
                {
                    CommandCallback callback = command_queue.Dequeue();
                    // Just respond with an empty string.
                    // Up to the receiving module to figure it out?
                    callback.response("");
                }
                    
            } else
            {
                command_queue.Clear();
            }
        }

        public static void SendCommand(CommandCallback commandCallback)
        {
            if(serialPort.IsOpen)
            {
                // Don't queue the callback if it doesn't have one - we'll be waiting for a packet that
                // doesn't have a response.
                if (commandCallback.response != null)
                {
                    command_queue.Enqueue(commandCallback);
                }
                serialPort.WriteLine(commandCallback.command);
                SwitchHardware.LogMessage("SerialDriver", "Sending Serial command: " + commandCallback.command);

            } else
            {
                // Do what here?
            }
        }

        private static string ToLiteral(string input)
        {
            using (var writer = new StringWriter())
            {
                using (var provider = CodeDomProvider.CreateProvider("CSharp"))
                {
                    provider.GenerateCodeFromExpression(new CodePrimitiveExpression(input), writer, null);
                    return writer.ToString();
                }
            }
        }

        private static void DataReceivedHandler(
                        object sender,
                        SerialDataReceivedEventArgs e)
        {
            SerialPort sp = (SerialPort)sender;
            string indata = sp.ReadExisting();
            if(indata != null && indata.Length != 0)
            {
                data_buffer += indata;
            }
            int end_packet_index = 0;
            // Keeps finding more packets in the data buffer.
            // If a packet isn't complete (i.e. we haven't seen \n),
            // we ignore it and wait for another DataReceived event.
            while (end_packet_index != -1 && data_buffer.Length != 0)
            {
                end_packet_index = data_buffer.IndexOf('\n');
                if(end_packet_index == -1)
                {
                    break;
                }
                //Substrings the current packet, and trims to remove whitespace.
                string packet = data_buffer.Substring(0, end_packet_index).Trim();
                SwitchHardware.LogMessage("SerialDriver", "Received Serial response: " + ToLiteral(packet));
                SwitchHardware.LogMessage("SerialDriver", "Current data buffer: " + ToLiteral(data_buffer));
                // Remove that packet from the buffer.
                // Next time we loop, we'll see a new packet in the buffer.
                data_buffer = data_buffer.Remove(0, end_packet_index + 1);

                // Now process the packet.
                if(command_queue.Count > 0)
                {
                    // Dequeue the latest command from the queue and respond to it.
                    CommandCallback callback = command_queue.Dequeue();
                    if(callback != null && callback.response != null)
                    {
                        callback.response(packet);
                        SwitchHardware.LogMessage("SerialDriver", "Responding to callback " + callback.command + " => " + packet);
                    }
                }
            }
        }
    }
}
