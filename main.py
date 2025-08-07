# Date: 8/25/23
import threading
import tkinter as tk
from tkinter import scrolledtext, messagebox, filedialog
import random
try:
    import RPi.GPIO as GPIO
except (RuntimeError, ModuleNotFoundError):
    # Use a mock GPIO library for development on non-Raspberry Pi systems
    import atexit
    from unittest.mock import MagicMock
    GPIO = MagicMock()
    atexit.register(GPIO.cleanup)


class AsicSimulator:
    def __init__(self, root):
        self.root = root
        self.root.title("IC Tester.")
        self.root.config(bg="#080202")
        self.root.geometry("780x830")

        # GPIO Pin Definitions
        self.socket1_good = 26
        self.socket1_bad = 20
        self.socket1_retest = 21
        self.socket1_recover = 19
        self.socket2_good = 13
        self.socket2_bad = 16
        self.socket2_retest = 6
        self.socket2_recover = 12
        self.START_PCB_ONE = 9
        self.START_PCB_TWO = 10
        self.START_TESTING = 11
        self.TESTING_COMPLETED = 5

        # Test Sockets
        self.TEST_SOCKET_1 = [self.socket1_good, self.socket1_bad, self.socket1_retest, self.socket1_recover]
        self.TEST_SOCKET_2 = [self.socket2_good, self.socket2_bad, self.socket2_retest, self.socket2_recover]

        # Name Dictionary
        self.names = {
            self.socket1_good: "Pass", self.socket1_bad: "Bad", self.socket1_retest: "Retest", self.socket1_recover: "Recover",
            self.socket2_good: "Pass", self.socket2_bad: "Bad", self.socket2_retest: "Retest", self.socket2_recover: "Recover"
        }

        # Application State
        self.selected_pcb_name_list = []
        self.test_completion_count = 0
        self.running = False

        # Constants
        self.TIME_DELAY_2_SECONDS = 2 * 1000
        self.ROOT_COLOR = "#080202"
        self.BOX_COLOR = "#EEEEEE"
        self.PCB_BUTTON_COLOR = "#176B87"

        # UI Variables
        self.pcb_vars = {f"PCB {i+1}": tk.BooleanVar(value=False) for i in range(4)}

        self.setup_gpio()
        self.create_widgets()

        self.status_display("Select PCB\nto\nStart Test")

    def setup_gpio(self):
        GPIO.setwarnings(False)
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(self.START_TESTING, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
        self.cleanup_pins()

    def cleanup_pins(self):
        pins = [
            *self.TEST_SOCKET_1,
            *self.TEST_SOCKET_2,
            self.START_PCB_ONE,
            self.START_PCB_TWO,
            self.TESTING_COMPLETED
        ]
        for pin in pins:
            GPIO.setup(pin, GPIO.OUT)
        print("Cleaned Up Pins")

    def create_widgets(self):
        # Main Title
        title_label = tk.Label(self.root, text="ASIC Simulator V-2.5", font=("SimSun", 32, "bold"), bg=self.ROOT_COLOR, fg="white")
        title_label.pack(pady=20)

        # Main Frame
        main_frame = tk.Frame(self.root, bg=self.ROOT_COLOR)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Left, Middle, and Right Frames
        left_frame = tk.Frame(main_frame, bg=self.ROOT_COLOR)
        left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5)
        middle_frame = tk.Frame(main_frame, bg=self.ROOT_COLOR)
        middle_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5)
        right_frame = tk.Frame(main_frame, bg=self.ROOT_COLOR)
        right_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5)

        # PCB Box Selector
        self.create_pcb_selector_box(left_frame)

        # Middle Box Display
        self.create_status_display_box(middle_frame)

        # Right Box Presser
        self.create_manual_testing_box(right_frame)

        # Main Output Text Box
        self.main_output_text_box = scrolledtext.ScrolledText(self.root, padx=10, background=self.BOX_COLOR, font=("arial", 14, "bold"),
                                                              height=14, width=50, borderwidth=2, relief=tk.SOLID)
        self.main_output_text_box.tag_configure('center', justify='center')
        self.main_output_text_box.pack(pady=10, fill=tk.BOTH, expand=True)

        # Button Frame
        button_frame = tk.Frame(self.root, bg=self.ROOT_COLOR)
        button_frame.pack(pady=10)

        # Save Log Button
        save_log_button = tk.Button(button_frame, text="Save Log", width=14, height=2, command=self.save_log, bg="#64CCC5")
        save_log_button.pack(side=tk.LEFT, padx=5)

        # Stop Button
        self.stop_button = tk.Button(button_frame, text="Stop", width=14, height=2, command=self.stop_test, bg="orange", state=tk.DISABLED)
        self.stop_button.pack(side=tk.LEFT, padx=5)

        # Exit Button
        button_exit = tk.Button(button_frame, text="Exit", width=14, height=2, command=self.destroy, bg="gray")
        button_exit.pack(side=tk.LEFT, padx=5)

    def create_pcb_selector_box(self, parent_frame):
        outer_frame = tk.Frame(parent_frame, bg=self.BOX_COLOR)
        outer_frame.pack(fill=tk.BOTH, expand=True)
        inner_frame = tk.Frame(outer_frame, bg=self.PCB_BUTTON_COLOR, bd=2, relief='solid')
        inner_frame.pack(fill=tk.BOTH, expand=True, padx=2, pady=2)

        label = tk.Label(inner_frame, text="Select PCB\n&\nStart Handshake", font=("SimSun", 11, "bold"), bg=self.PCB_BUTTON_COLOR, fg="white")
        label.pack(pady=5)

        for name, var in self.pcb_vars.items():
            cb = tk.Checkbutton(inner_frame, text=name, width=8, height=2, variable=var, bg=self.PCB_BUTTON_COLOR)
            cb.pack(pady=2)

        self.start_button = tk.Button(inner_frame, text="Start Loop", width=16, height=2, command=self.start_signal_thread, bg="#64CCC5")
        self.start_button.pack(pady=10)

    def create_status_display_box(self, parent_frame):
        outer_frame = tk.Frame(parent_frame, bg=self.BOX_COLOR)
        outer_frame.pack(fill=tk.BOTH, expand=True)
        inner_frame = tk.Frame(outer_frame, bg=self.PCB_BUTTON_COLOR, bd=2, relief='solid')
        inner_frame.pack(fill=tk.BOTH, expand=True, padx=2, pady=2)

        label = tk.Label(inner_frame, text="Current Test\nStatus", font=("SimSun", 11, "bold"), bg=self.PCB_BUTTON_COLOR, fg="white")
        label.pack(pady=5)

        self.status_output_text_box = scrolledtext.ScrolledText(inner_frame, background=self.BOX_COLOR, font=("arial", 14, "bold"), height=6,
                                                                width=11, borderwidth=2, relief=tk.SOLID)
        self.status_output_text_box.tag_configure('center', justify='center', foreground="red")
        self.status_output_text_box.pack(pady=5, padx=5, fill=tk.BOTH, expand=True)

    def create_manual_testing_box(self, parent_frame):
        outer_frame = tk.Frame(parent_frame, bg=self.BOX_COLOR)
        outer_frame.pack(fill=tk.BOTH, expand=True)
        inner_frame = tk.Frame(outer_frame, bg=self.PCB_BUTTON_COLOR, bd=2, relief='solid')
        inner_frame.pack(fill=tk.BOTH, expand=True, padx=2, pady=2)

        label = tk.Label(inner_frame, text="Manual\nTesting", font=("SimSun", 11, "bold"), bg=self.PCB_BUTTON_COLOR, fg="white")
        label.pack(pady=5)

        tests = {
            "All Passed": ("good", "green"),
            "All Failed": ("bad", "red"),
            "Retest All": ("retest", "#79AC78"),
            "Recover All": ("recover", "#FF9B50"),
            "Randomize": ("random", "#F8FF95")
        }

        for text, (test_type, color) in tests.items():
            button = tk.Button(inner_frame, text=text, width=10, height=1, command=lambda t=test_type: self.run_manual_test_thread(t), bg=color)
            button.pack(pady=5)

    def status_display(self, new_msg):
        self.status_output_text_box.delete(1.0, tk.END)
        self.status_output_text_box.insert(tk.END, new_msg, "center")
        self.status_output_text_box.update()

    def get_checked_pcbs(self):
        return [name for name, var in self.pcb_vars.items() if var.get()]

    def signal_start(self):
        self.selected_pcb_name_list = self.get_checked_pcbs()
        if not self.selected_pcb_name_list:
            messagebox.showwarning("Warning!", "Must select at least one PCB")
            return

        self.running = True
        self.start_button.config(state=tk.DISABLED)
        self.stop_button.config(state=tk.NORMAL)

        counter = 0
        while self.running:
            self.status_display(f"Waiting\nfor\nP&P!\n\n{counter}")
            counter += 1
            self.root.update()
            self.root.after(1000)
            if GPIO.input(self.START_TESTING) == GPIO.LOW:
                self.status_display("Testing\nIn\nProgress")
                self.root.update()
                self.root.after(1000)
                self.start_automate_handshake_thread()
                break

    def automate_handshake(self):
        if not self.running:
            return

        self.test_completion_count += 1
        random.shuffle(self.TEST_SOCKET_1)
        random.shuffle(self.TEST_SOCKET_2)
        self.main_output_text_box.insert(tk.END, f"Test Number: {self.test_completion_count}\n\n", "center")
        self.main_output_text_box.update()

        pcb_to_test = self.selected_pcb_name_list.pop(0)

        pin_one = self.TEST_SOCKET_1[random.randint(0, 3)]
        pin_two = self.TEST_SOCKET_2[random.randint(0, 3)]
        GPIO.output(pin_one, GPIO.LOW)
        GPIO.output(pin_two, GPIO.LOW)
        self.main_output_text_box.insert(tk.END, f"{pcb_to_test}:\nSocket 1 Test: {self.names[pin_one]}\n")
        self.main_output_text_box.insert(tk.END, f"Socket 2 Test: {self.names[pin_two]}\n\n")
        self.main_output_text_box.update()
        self.root.after(self.TIME_DELAY_2_SECONDS)
        GPIO.output(pin_one, GPIO.HIGH)
        GPIO.output(pin_two, GPIO.HIGH)
        self.root.after(self.TIME_DELAY_2_SECONDS)

        if not self.selected_pcb_name_list:
            message = f"\n------------------------------------------------------------------------------------\n" \
                      f"                      Test {self.test_completion_count} Has been completed                    " \
                      f"\n------------------------------------------------------------------------------------\n\n"
            self.main_output_text_box.insert(tk.END, message, "center")
            self.main_output_text_box.update()
            self.status_display(f"Test {self.test_completion_count}\ncompleted")
            self.start_button.config(state=tk.NORMAL)
            self.stop_button.config(state=tk.DISABLED)
            self.running = False
        else:
            self.start_automate_handshake_thread()

    def run_manual_test(self, test_type):
        if self.running:
            messagebox.showwarning("Warning!", "A test is already in progress.")
            return

        selected_pcbs = self.get_checked_pcbs()
        if not selected_pcbs:
            messagebox.showwarning("Warning!", "Must select at least one PCB")
            return

        self.running = True
        self.start_button.config(state=tk.DISABLED)
        self.stop_button.config(state=tk.NORMAL)

        self.test_completion_count += 1
        self.main_output_text_box.insert(tk.END, f"Current Test Number: {self.test_completion_count}\n\n", "center")
        self.main_output_text_box.update()
        self.root.after(self.TIME_DELAY_2_SECONDS)

        for pcb_name in selected_pcbs:
            if not self.running:
                break
            socket1_pin, socket2_pin, result_text = self.get_test_pins_and_text(test_type)

            GPIO.output(socket1_pin, GPIO.LOW)
            GPIO.output(socket2_pin, GPIO.LOW)

            message = f"{pcb_name}:\nSocket 1. Test Result: {result_text}\nSocket 2. Test Result: {result_text}\n\n"
            self.main_output_text_box.insert(tk.END, message)
            self.main_output_text_box.update()

            self.root.after(self.TIME_DELAY_2_SECONDS)

            GPIO.output(socket1_pin, GPIO.HIGH)
            GPIO.output(socket2_pin, GPIO.HIGH)

        message = f"\n------------------------------------------------------------------------------------\n" \
                  f" -                     Test {self.test_completion_count} Has been completed                          - " \
                  f"\n------------------------------------------------------------------------------------\n\n"
        self.main_output_text_box.insert(tk.END, message, "center")
        self.main_output_text_box.update()
        self.status_display(f"Test {self.test_completion_count}\ncompleted")
        self.start_button.config(state=tk.NORMAL)
        self.stop_button.config(state=tk.DISABLED)
        self.running = False

    def get_test_pins_and_text(self, test_type):
        if test_type == "good":
            return self.socket1_good, self.socket2_good, "PASS"
        elif test_type == "bad":
            return self.socket1_bad, self.socket2_bad, "Failed"
        elif test_type == "retest":
            return self.socket1_retest, self.socket2_retest, "Retest"
        elif test_type == "recover":
            return self.socket1_recover, self.socket2_recover, "Recover"
        elif test_type == "random":
            pin1 = self.TEST_SOCKET_1[random.randint(0, 3)]
            pin2 = self.TEST_SOCKET_2[random.randint(0, 3)]
            return pin1, pin2, f"{self.names[pin1]}/{self.names[pin2]}"


    def start_signal_thread(self):
        threading.Thread(target=self.signal_start, daemon=True).start()

    def start_automate_handshake_thread(self):
        threading.Thread(target=self.automate_handshake, daemon=True).start()

    def run_manual_test_thread(self, test_type):
        threading.Thread(target=self.run_manual_test, args=(test_type,), daemon=True).start()

    def stop_test(self):
        self.running = False
        self.start_button.config(state=tk.NORMAL)
        self.stop_button.config(state=tk.DISABLED)
        self.status_display("Test\nStopped")

    def save_log(self):
        log_content = self.main_output_text_box.get(1.0, tk.END)
        if not log_content.strip():
            messagebox.showwarning("Warning!", "Log is empty.")
            return

        file_path = tk.filedialog.asksaveasfilename(defaultextension=".txt", filetypes=[("Text files", "*.txt"), ("All files", "*.*")])
        if file_path:
            with open(file_path, "w") as f:
                f.write(log_content)
            messagebox.showinfo("Success", "Log saved successfully.")

    def destroy(self):
        GPIO.cleanup()
        self.root.destroy()


if __name__ == "__main__":
    root = tk.Tk()
    app = AsicSimulator(root)
    root.mainloop()
