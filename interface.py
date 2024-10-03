import gradio as gr
import serial
import serial.tools.list_ports
import threading
import time
import pandas as pd


# Global variables
ser = None
receive_thread = None
running = False

# Function to list available COM ports
def list_com_ports():
    ports = serial.tools.list_ports.comports()
    return [port.device for port in ports]

def get_commands():
    df = pd.read_csv('commands.csv')
    return df

class Interface:
    def __init__(self):
        com_ports = list_com_ports()
        commands = get_commands()
        baudrates = [9600, 14400, 19200, 38400, 57600, 115200]
        with gr.Blocks() as self.demo:
            with gr.Tab("串口连接"):
                gr.Markdown("### 串口连接")
                with gr.Row():
                    self.port_dropdown = gr.Dropdown(label="端口", choices=com_ports,
                                                     value=com_ports[0] if com_ports else None)
                    self.baudrate_dropdown = gr.Dropdown(label="波特率", choices=baudrates,
                                                         value=baudrates[0])
                    self.connect_button = gr.Button("连接")

                with gr.Row():
                    self.command_dropdown = gr.Dropdown(label="命令", choices=commands['name'].to_list())
                    self.send_button = gr.Button("发送")
                self.receive_box = gr.Textbox(label="信息", interactive=False, lines=10)

            with gr.Tab("系统信息"):
                version = "0.1.0"
                measure_range = "0-100"
                gr.Markdown("### Serial Connection Info")
                gr.Markdown("This is a simple interface to connect to a serial port and send commands to it. "
                            "You can select the COM port and baud rate from the dropdowns and click the Connect button to establish a connection. "
                            "Once connected, you can select a command from the dropdown and click the Send button to send it to the serial port. "
                            "The received messages will be displayed in the text box below.")
                gr.Markdown(f"版本: {version}")
                gr.Markdown(f"量程: {measure_range}")
            # Set up the connection logic
            self.connect_button.click(
                self.connect_port,
                inputs=[self.port_dropdown, self.baudrate_dropdown],
                outputs=[]
            )
            self.send_button.click(
                self.send_messages,
                inputs=[self.command_dropdown],
                outputs=self.receive_box
            )

    def connect_port(self, port, baudrate):
        global ser, running, receive_thread
        try:
            if running == False:
                ser = serial.Serial(port, baudrate)
                running = True

                # Start the receiving thread
                receive_thread = threading.Thread(target=self.receive_messages)
                receive_thread.start()

                return f"Connected to {port} at {baudrate} baud rate successfully."
            else:  # disconnect the current connection
                self.connect_button.label = "Disconnect"
                receive_thread.join()
                ser.close()
                running = False

                return f"Disconnected from {port}."

        except Exception as e:
            return f"Failed to connect: {str(e)}"


    # Function to receive messages from the serial port
    def receive_messages(self):
        global ser, running
        while running:
            if ser.in_waiting > 0:
                message = ser.readline().decode('utf-8').strip()
                gr.update(self.receive_box, message)  # Update the receive box with the message

    def send_messages(self, message):
        global ser, running
        while running:
            if ser.in_waiting > 0:
                ser.write(message.encode('utf-8'))

    def launch(self):
        self.demo.launch()
