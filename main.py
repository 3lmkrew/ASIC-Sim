# Date: 8/25/23
import threading
import tkinter as tk
import RPi.GPIO as GPIO
from tkinter import scrolledtext, messagebox
import random

# Define GPIO pines for socket # 1
socket1_good = 26
socket1_bad = 20
socket1_retest = 21
socket1_recover = 19
# Define GPIO pines for socket # 2
socket2_good = 13
socket2_bad = 16
socket2_retest = 6
socket2_recover = 12

# Output pins to inform current testing PCB number (1, 2, 3 or 4)
START_PCB_ONE = 9
START_PCB_TWO = 10

# Input start testing signal, expects 3.3 volts to activate, signal send from P&P and Read by Raspberry Pi.
START_TESTING = 11

# Output testing completed signal
TESTING_COMPLETED = 5

# Name Dictionary
names = {26: "Pass", 20: "Bad", 21: "Retest", 19: "Recover", 13: "Pass", 16: "Bad", 6: "Retest", 12: "Recover"}
TEST_SOCKET_1 = [socket1_good, socket1_bad, socket1_retest, socket1_recover]
TEST_SOCKET_2 = [socket2_good, socket2_bad, socket2_retest, socket2_recover]
selected_pcb_name_list = []  # Will append selected PCB from checked box
TEST_COMPLETION_COUNT = 0
TIME_DELAY_6_SECONDS = 2 * 1000  # This would equal 6 seconds

# set up gpio pins
GPIO.setwarnings(False)
GPIO.setmode(GPIO.BCM)

# Set the Input pins
GPIO.setup(START_TESTING, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)  # Setting the input pin with a pull-down resistor


# Set up the Output pins
def clean_up_pcb():
    # 8 Channel relay board activates all channels when powered on, this will power them off.
    GPIO.setup(socket1_good, GPIO.OUT)
    GPIO.setup(socket1_bad, GPIO.OUT)
    GPIO.setup(socket1_retest, GPIO.OUT)
    GPIO.setup(socket1_recover, GPIO.OUT)
    GPIO.setup(socket2_good, GPIO.OUT)
    GPIO.setup(socket2_bad, GPIO.OUT)
    GPIO.setup(socket2_retest, GPIO.OUT)
    GPIO.setup(socket2_recover, GPIO.OUT)
    GPIO.setup(START_PCB_ONE, GPIO.OUT)
    GPIO.setup(START_PCB_TWO, GPIO.OUT)
    GPIO.setup(TESTING_COMPLETED, GPIO.OUT)
    print("Clean UP PCB")


clean_up_pcb()


def extract_and_sort_numbers(combination_list):
    numbers = []
    for item in combination_list:
        # Extract numbers from the string using a list comprehension and join to form the full number
        number_str = ''.join([char for char in item if char.isdigit()])
        if number_str:  # If a number is found
            numbers.append(int(number_str))
    return sorted(numbers)


def checked_boxes():
    """PCB 1 to 4 are boolean variable set to false but if button PCB 1 is checked it will change to True
       when clicking on start test button, it will run signal start function that will immediately call this function
        will check the 4 buttons for boolem and append only True to global PCB Activation list and return list"""
    global selected_pcb_name_list  # empty list.
    pcb_checkbox = [pcb1.get(), pcb2.get(), pcb3.get(), pcb4.get()]  # Sample if 2 & 4: [False, True, False, True]
    for _ in pcb_checkbox:
        if pcb_checkbox[0] and "PCB 1" not in selected_pcb_name_list:
            selected_pcb_name_list.append("PCB 1")
            pcb1.set(True)
        elif pcb_checkbox[1] and "PCB 2" not in selected_pcb_name_list:
            selected_pcb_name_list.append("PCB 2")
            pcb2.set(True)
        elif pcb_checkbox[2] and "PCB 3" not in selected_pcb_name_list:
            selected_pcb_name_list.append("PCB 3")
            pcb3.set(True)  # removes check marks from box #3
        elif pcb_checkbox[3] and "PCB 4" not in selected_pcb_name_list:
            selected_pcb_name_list.append("PCB 4")
            pcb4.set(True)  # removes check marks from box #4
    sorted_list = extract_and_sort_numbers(selected_pcb_name_list)
    return sorted_list  # Sample if selected checkbox 2 and 4: [2, 4]


def status_display(new_msg):
    status_output_text_box.delete(1.0, tk.END)  # Clear the ScrolledText content
    status_output_text_box.insert(tk.END, new_msg, "center")  # Insert the new message
    status_output_text_box.update()


def signal_start():
    global TEST_COMPLETION_COUNT  # Starts with int = 0
    global selected_pcb_name_list  # PCB_X selection from checked box
    checked_boxes()  # start check_box function to determine PCB selection
    counter_for_test_only = 0  # counter only for testing
    while True:
        status_display(f"Waiting\nfor\nP&P!\n\n{counter_for_test_only}")
        counter_for_test_only += 1
        root.after(1000)
        if GPIO.input(START_TESTING) == GPIO.LOW and len(selected_pcb_name_list) >= 1:
            # if counter_for_test_only == 2 and len(selected_pcb_name_list) >= 1:
            status_display(f"Testing\nIn\nProgress")
            root.after(1000)
            automate_handshake_threading()
            break
        if len(selected_pcb_name_list) == 0:
            messagebox.showwarning("Warning!", "Must select at least one PCB")
            break


def automate_handshake():
    global TEST_SOCKET_1
    global TEST_SOCKET_2
    global selected_pcb_name_list
    global TEST_COMPLETION_COUNT
    global status_title_label
    if TEST_COMPLETION_COUNT == 0:
        TEST_COMPLETION_COUNT += 1
    else:
        TEST_COMPLETION_COUNT += 1
    random.shuffle(TEST_SOCKET_1)  # Shuffle PCB_1_list & PCB_2_list
    random.shuffle(TEST_SOCKET_2)
    main_output_text_box.insert(tk.END, f"Test Number: {TEST_COMPLETION_COUNT}\n\n", "center")
    main_output_text_box.update()
    try:
        while True:
            for item in range(len(selected_pcb_name_list)):
                if selected_pcb_name_list[item] == "PCB 1":
                    # PCB 1 Go.
                    pin_one = TEST_SOCKET_1[random.randint(0, 3)]  # select random test result for socket 1
                    pin_two = TEST_SOCKET_2[random.randint(0, 3)]  # select random test result for socket 2
                    GPIO.output(pin_one, GPIO.LOW)  # outputs test results to socket 1 by sending 5 volts to IO port
                    GPIO.output(pin_two, GPIO.LOW)  # outputs test results to socket 2 by sending 5 volts to IO port
                    main_output_text_box.insert(tk.END, f"PCB 1:\nSocket 1 Test: {names[pin_one]}\n")
                    main_output_text_box.insert(tk.END, f"Socket 2 Test: {names[pin_two]}\n\n")
                    main_output_text_box.update()
                    root.after(TIME_DELAY_6_SECONDS)
                    GPIO.output(pin_two, GPIO.HIGH)  # OFF
                    GPIO.output(pin_one, GPIO.HIGH)  # OFF
                    root.after(TIME_DELAY_6_SECONDS)
                    selected_pcb_name_list.pop(0)
                    break
                    # PCB 2 Go.
                elif selected_pcb_name_list[item] == "PCB 2":
                    pin_one = TEST_SOCKET_1[random.randint(0, 3)]  # select random test result for socket 1
                    pin_two = TEST_SOCKET_2[random.randint(0, 3)]  # select random test result for socket 2
                    GPIO.output(pin_one, GPIO.LOW)  # outputs test results to socket 1 by sending 5 volts to IO port
                    GPIO.output(pin_two, GPIO.LOW)  # outputs test results to socket 2 by sending 5 volts to IO port
                    main_output_text_box.insert(tk.END, f"PCB 2:\nSocket 1 Test: {names[pin_one]}\n")
                    main_output_text_box.insert(tk.END, f"Socket 2 Test: {names[pin_two]}\n\n")
                    main_output_text_box.update()
                    root.after(TIME_DELAY_6_SECONDS)
                    GPIO.output(pin_two, GPIO.HIGH)  # OFF
                    GPIO.output(pin_one, GPIO.HIGH)  # OFF
                    root.after(TIME_DELAY_6_SECONDS)
                    selected_pcb_name_list.pop(0)
                    break

                    # PCB 3 Go.
                elif selected_pcb_name_list[item] == "PCB 3":
                    pin_one = TEST_SOCKET_1[random.randint(0, 3)]  # select random test result for socket 1
                    pin_two = TEST_SOCKET_2[random.randint(0, 3)]  # select random test result for socket 2
                    # outputs test results to socket 1 by sending 5 volts to IO port
                    GPIO.output(pin_one, GPIO.LOW)  # outputs test results to socket 1 by sending 5 volts to IO port
                    GPIO.output(pin_two, GPIO.LOW)  # outputs test results to socket 2 by sending 5 volts to IO port
                    main_output_text_box.insert(tk.END, f"PCB 3:\nSocket 1 Test: {names[pin_one]}\n")
                    main_output_text_box.insert(tk.END, f"Socket 2 Test: {names[pin_two]}\n\n")
                    main_output_text_box.update()
                    root.after(TIME_DELAY_6_SECONDS)
                    GPIO.output(pin_two, GPIO.HIGH)  # OFF
                    GPIO.output(pin_one, GPIO.HIGH)  # OFF
                    root.after(TIME_DELAY_6_SECONDS)
                    selected_pcb_name_list.pop(0)
                    break

                # PCB 4 Go.
                elif selected_pcb_name_list[item] == "PCB 4":
                    pin_one = TEST_SOCKET_1[random.randint(0, 3)]  # select random test result for socket 1
                    pin_two = TEST_SOCKET_2[random.randint(0, 3)]  # select random test result for socket 2
                    GPIO.output(pin_one, GPIO.LOW)  # outputs test results to socket 1 by sending 5 volts to IO port
                    GPIO.output(pin_two, GPIO.LOW)  # outputs test results to socket 2 by sending 5 volts to IO port
                    main_output_text_box.insert(tk.END, f"PCB 4:\nSocket 1 Test: {names[pin_one]}\n")
                    main_output_text_box.insert(tk.END, f"Socket 2 Test: {names[pin_two]}\n\n")
                    main_output_text_box.update()
                    root.after(TIME_DELAY_6_SECONDS)
                    GPIO.output(pin_two, GPIO.HIGH)  # OFF
                    GPIO.output(pin_one, GPIO.HIGH)  # OFF
                    root.after(TIME_DELAY_6_SECONDS)
                    selected_pcb_name_list.pop(0)
                    break
            if len(selected_pcb_name_list) < 1:
                break
        message = f"\n------------------------------------------------------------------------------------\n" \
                  f"                      Test {TEST_COMPLETION_COUNT} Has been completed                    " \
                  f"\n------------------------------------------------------------------------------------\n\n"
        main_output_text_box.insert(tk.END, message, "center")
        root.after(1000)
        main_output_text_box.update()
        status_display(f"Test {TEST_COMPLETION_COUNT}\ncompleted")
        status_output_text_box.update()
        signal_start_threading()
    except TypeError:
        print("I'm inside the except block")
    finally:
        print(f"I'm inside the finally block")


def start_all_good():
    global TEST_COMPLETION_COUNT
    pcb_number_dic = {"PCB 1": 1, "PCB 2": 2, "PCB 3": 3, "PCB 4": 4}
    TEST_COMPLETION_COUNT += 1
    selected_pcb = checked_boxes()
    test_count = 0
    status_display(f"Waiting\nfor\nP&P!")
    while True:
        test_count += 1
        root.after(1000)
        # if GPIO.input(START_TESTING) == GPIO.LOW and len(PCB_ACTIVATION) >= 1:
        if test_count == 5 and len(selected_pcb) >= 1:
            status_display(f"Testing\nIn\nProgress")
            break
    main_output_text_box.insert(tk.END, f"Current Test Number: {TEST_COMPLETION_COUNT}\n\n", "center")
    main_output_text_box.update()
    root.after(TIME_DELAY_6_SECONDS)
    for index, item in enumerate(selected_pcb, start=1):
        message_good = f"PCB {pcb_number_dic[item]}:\nSocket 1. Test Result: PASS\nSocket 2. Test Result: PASS\n\n"
        GPIO.output(socket1_good, GPIO.LOW)
        GPIO.output(socket2_good, GPIO.LOW)
        main_output_text_box.insert(tk.END, f"{message_good}")
        main_output_text_box.update()
        root.after(TIME_DELAY_6_SECONDS)
        GPIO.output(socket1_good, GPIO.HIGH)  # Control the Channel 1
        GPIO.output(socket2_good, GPIO.HIGH)  # Control the Channel 6
    message = f"\n------------------------------------------------------------------------------------\n" \
              f" -                     Test {TEST_COMPLETION_COUNT} Has been completed                          - " \
              f"\n------------------------------------------------------------------------------------\n\n"
    del selected_pcb[:]
    main_output_text_box.insert(tk.END, message, "center")
    root.after(1000)
    main_output_text_box.update()
    status_display(f"Test {TEST_COMPLETION_COUNT}\ncompleted")
    status_output_text_box.update()
    m = threading.Thread(target=signal_start)
    m.start()


def start_all_bad():
    global TEST_COMPLETION_COUNT
    pcb_number_dic = {"PCB 1": 1, "PCB 2": 2, "PCB 3": 3, "PCB 4": 4}
    TEST_COMPLETION_COUNT += 1
    selected_pcb = checked_boxes()
    main_output_text_box.insert(tk.END, f"Current Test Number: {TEST_COMPLETION_COUNT}\n\n", "center")
    root.after(TIME_DELAY_6_SECONDS)
    for index, item in enumerate(selected_pcb, start=1):
        message_failed = f"PCB {pcb_number_dic[item]}:\nSocket 1. Test Result: Failed\nSocket 2 Test Result: Failed\n\n"
        GPIO.output(socket1_bad, GPIO.LOW)
        GPIO.output(socket2_bad, GPIO.LOW)
        main_output_text_box.insert(tk.END, f"{message_failed}")
        main_output_text_box.update()
        root.after(TIME_DELAY_6_SECONDS)
        GPIO.output(socket1_bad, GPIO.HIGH)  # Control the Channel 1
        GPIO.output(socket2_bad, GPIO.HIGH)  # Control the Channel 6
    message = f"\n------------------------Test {TEST_COMPLETION_COUNT} Has been completed----------------------\n\n"
    del selected_pcb[:]
    main_output_text_box.insert(tk.END, message, "center")
    root.after(1000)
    main_output_text_box.update()


def start_all_retest():
    global TEST_COMPLETION_COUNT
    pcb_number_dic = {"PCB 1": 1, "PCB 2": 2, "PCB 3": 3, "PCB 4": 4}
    TEST_COMPLETION_COUNT += 1
    selected_pcb = checked_boxes()
    main_output_text_box.insert(tk.END, f"Current Test Number: {TEST_COMPLETION_COUNT}\n\n", "center")
    root.after(TIME_DELAY_6_SECONDS)
    for index, item in enumerate(selected_pcb, start=1):
        message_retest = f"PCB {pcb_number_dic[item]}:\nSocket 1. Test Result: Retest\nSocket 2 Test Result: Retest\n\n"
        print(f"Setting GPIO pin {names[socket1_retest]} to value GPIO.LOW")  # Control the Channel 1
        GPIO.output(socket1_retest, GPIO.LOW)
        GPIO.output(socket2_retest, GPIO.LOW)
        main_output_text_box.insert(tk.END, f"{message_retest}")
        main_output_text_box.update()
        root.after(TIME_DELAY_6_SECONDS)
        GPIO.output(socket1_retest, GPIO.HIGH)  # Control the Channel 1
        GPIO.output(socket2_retest, GPIO.HIGH)  # Control the Channel 6
    message = f"\n------------------------------------------------------------------------------------\n" \
              f" -                     Test {TEST_COMPLETION_COUNT} Has been completed                          - " \
              f"\n------------------------------------------------------------------------------------\n\n"
    del selected_pcb[:]
    main_output_text_box.insert(tk.END, message, "center")
    root.after(1000, status_display(f"Select PCB\nto\nStart Test"))
    main_output_text_box.update()


def start_all_recover():
    global TEST_COMPLETION_COUNT
    pcb_number_dic = {"PCB 1": 1, "PCB 2": 2, "PCB 3": 3, "PCB 4": 4}
    TEST_COMPLETION_COUNT += 1
    selected_pcb = checked_boxes()
    main_output_text_box.insert(tk.END, f"Current Test Number: {TEST_COMPLETION_COUNT}\n\n", "center")
    root.after(TIME_DELAY_6_SECONDS)
    for index, item in enumerate(selected_pcb, start=1):
        message_recover = f"PCB {pcb_number_dic[item]}:\nSocket 1.Test Result:Recover\nSocket 2 Test Result:Recover\n\n"
        GPIO.output(socket1_recover, GPIO.LOW)
        GPIO.output(socket2_recover, GPIO.LOW)
        main_output_text_box.insert(tk.END, f"{message_recover}")
        main_output_text_box.update()
        root.after(TIME_DELAY_6_SECONDS)
        GPIO.output(socket1_recover, GPIO.HIGH)  # Control the Channel 1
        GPIO.output(socket2_recover, GPIO.HIGH)  # Control the Channel 6
    message = f"\n------------------------------------------------------------------------------------\n" \
              f" -                     Test {TEST_COMPLETION_COUNT} Has been completed                 - " \
              f"\n------------------------------------------------------------------------------------\n\n"
    del selected_pcb[:]
    main_output_text_box.insert(tk.END, message, "center")
    root.after(1000)
    main_output_text_box.update()


def random_signals():
    # Randomly selects: good, bad, retest, recover and sends IO signal to selected channel
    global TEST_SOCKET_1
    global TEST_SOCKET_2
    global TEST_COMPLETION_COUNT
    TEST_COMPLETION_COUNT += 1
    try:
        while True:
            random.shuffle(TEST_SOCKET_1)  # Shuffle PCB_1_list & PCB_2_list
            random.shuffle(TEST_SOCKET_2)
            main_output_text_box.insert(tk.END, f"Current Test Number: {TEST_COMPLETION_COUNT}\n\n", "center")
            # PCB 1
            pin_one = TEST_SOCKET_1[random.randint(0, 3)]  # pick and random index from list #1
            pin_two = TEST_SOCKET_2[random.randint(0, 3)]  # pick and random number from list #2
            print(f"Setting GPIO pin pin_one to value GPIO.LOW")  # ON
            print(f"Setting GPIO pin pin_two to value GPIO.LOW")  # ON
            main_output_text_box.insert(tk.END, f"PCB 1:\nSocket 1. Test Result: {names[pin_one]}\n")
            main_output_text_box.insert(tk.END, f"Socket 2. Test Result: {names[pin_two]}\n\n")
            root.after(TIME_DELAY_6_SECONDS)  # random time 10 seconds
            print(f"Setting GPIO pin pin_two to value GPIO.HIGH")  # OFF
            print(f"Setting GPIO pin pin_one to value GPIO.HIGH")  # OFF
            message = f"\n------------------------------------------------------------------------------------\n" \
                      f" -                     Test {TEST_COMPLETION_COUNT} Has been completed                 - " \
                      f"\n------------------------------------------------------------------------------------\n\n"
            main_output_text_box.insert(tk.END, message, "center")
            root.after(1000)
            main_output_text_box.update()

            break
    finally:
        print(f"Random test {TEST_COMPLETION_COUNT}")


def destroy():
    root.destroy()


#####################################################################################################################
# -------------------------------------------TKINTER GUI STARTS HERE------------------------------------------------#
#####################################################################################################################

ROOT_COLOR = "#080202"
BOX_COLOR = "#EEEEEE"
PCB_BUTTON_COLOR = "#176B87"
root = tk.Tk()  # Create the GUI window
root.title("IC Tester.")
root.config(bg=ROOT_COLOR)
root.geometry("780x830")

# create a main title label
title_label = tk.Label(root, text="ASIC Simulator V-2.5", font=("SimSun", 32, "bold"), bg=ROOT_COLOR, fg="white")
title_label.place(x=150, y=45)

#####################################################################################################################
# -------------------------------------------PCB BOX SELECTOR------------------------------------------------#
#####################################################################################################################
outer_frame = tk.Frame(root, bg='#EEEEEE')
outer_frame.place(x=100, y=150, width=170, height=270)
# Create an inner frame with the desired background color and place it inside the outer frame
inner_frame = tk.Frame(outer_frame, bg='#176B87', bd=2, relief='solid')
inner_frame.place(x=2, y=2, width=166, height=266)  # 2 pixels smaller on each side

PCB_checkbox_label = tk.Label(inner_frame, text="Select PCB\n&\nStart Handshake", font=("SimSun", 11, "bold"),
                              bg='#176B87', fg="white")
PCB_checkbox_label.place(x=12, y=2)

#####################################################################################################################
# -------------------------------------------MIDDLE BOX DISPLAY------------------------------------------------#
#####################################################################################################################


outer_frame_3 = tk.Frame(root, bg='#EEEEEE')
outer_frame_3.place(x=300, y=150, width=170, height=270)
# Create an inner frame with the desired background color and place it inside the outer frame
inner_frame_3 = tk.Frame(outer_frame_3, bg='#176B87', bd=2, relief='solid')
inner_frame_3.place(x=2, y=2, width=166, height=266)  # 2 pixels smaller on each side

status_title_label = tk.Label(inner_frame_3, text="Current Test\nStatus", font=("SimSun", 11, "bold"),
                              bg='#176B87', fg="white")
status_title_label.place(x=25, y=3)

#####################################################################################################################
# -------------------------------------------RIGHT BOX PRESSER------------------------------------------------#
#####################################################################################################################

outer_frame_2 = tk.Frame(root, bg='#EEEEEE')
outer_frame_2.place(x=500, y=150, width=170, height=270)
# Create an inner frame with the desired background color and place it inside the outer frame
inner_frame_2 = tk.Frame(outer_frame_2, bg='#176B87', bd=2, relief='solid')
inner_frame_2.place(x=2, y=2, width=166, height=266)  # 2 pixels smaller on each side

MANUAL_BUTTONS_label = tk.Label(inner_frame_2, text="Manual\nTesting", font=("SimSun", 11, "bold"),
                                bg='#176B87', fg="white")
MANUAL_BUTTONS_label.place(x=45, y=3)


######################################################################################################################

def signal_start_threading():
    t = threading.Thread(target=signal_start)
    t.start()


def automate_handshake_threading():
    t = threading.Thread(target=automate_handshake)
    t.start()


def all_good_loop():
    a = threading.Thread(target=start_all_good)
    a.start()


######################################################################################################################
# Create a button widget
button_pass = tk.Button(inner_frame_2, text="All Passed", width=10, height=1, command=all_good_loop, bg="green")
button_fail = tk.Button(inner_frame_2, text="All Failed", width=10, height=1, command=start_all_bad, bg="red")
button_retest = tk.Button(inner_frame_2, text="Retest All", width=10, height=1, command=start_all_retest, bg="#79AC78")
button_recover = tk.Button(inner_frame_2, text="Recover All", width=10, height=1, command=start_all_recover,
                           bg="#FF9B50")
button_random = tk.Button(inner_frame_2, text="Randomize", width=10, height=1, command=random_signals, bg="#F8FF95")

button_exit = tk.Button(root, text="Exit", width=14, height=2, command=destroy, bg="gray")

button_pass.place(x=80, y=70, anchor=tk.CENTER)
button_fail.place(x=80, y=110, anchor=tk.CENTER)
button_retest.place(x=80, y=150, anchor=tk.CENTER)
button_recover.place(x=80, y=190, anchor=tk.CENTER)
button_random.place(x=80, y=230, anchor=tk.CENTER)
button_exit.place(x=620, y=795, anchor=tk.CENTER)

pcb1 = tk.BooleanVar(value=False)
pcb2 = tk.BooleanVar(value=False)
pcb3 = tk.BooleanVar(value=False)
pcb4 = tk.BooleanVar(value=False)

check_box1 = tk.Checkbutton(inner_frame, text="PCB 1", width=8, height=2, variable=pcb1, bg=PCB_BUTTON_COLOR)
check_box2 = tk.Checkbutton(inner_frame, text="PCB 2", width=8, height=2, variable=pcb2, bg=PCB_BUTTON_COLOR)
check_box3 = tk.Checkbutton(inner_frame, text="PCB 3", width=8, height=2, variable=pcb3, bg=PCB_BUTTON_COLOR)
check_box4 = tk.Checkbutton(inner_frame, text="PCB 4", width=8, height=2, variable=pcb4, bg=PCB_BUTTON_COLOR)

check_box1.place(x=35, y=60)
check_box2.place(x=35, y=90)
check_box3.place(x=35, y=120)
check_box4.place(x=35, y=150)

start_loop = tk.Button(inner_frame, text="Start Loop", width=16, height=2, command=signal_start, bg="#64CCC5")
start_loop.place(x=80, y=220, anchor=tk.CENTER)

main_output_text_box = scrolledtext.ScrolledText(root, padx=10, background=BOX_COLOR, font=("arial", 14, "bold"),
                                                 height=14,
                                                 width=50, borderwidth=2, relief=tk.SOLID)
main_output_text_box.tag_configure('center', justify='center')
main_output_text_box.place(x=80, y=455)

status_output_text_box = scrolledtext.ScrolledText(root, background=BOX_COLOR, font=("arial", 14, "bold"), height=6,
                                                   width=11, borderwidth=2, relief=tk.SOLID)
status_output_text_box.tag_configure('center', justify='center', foreground="red")
status_output_text_box.place(x=312, y=240)

root.after(1000, status_display(f"Select PCB\nto\nStart Test"))

root.mainloop()
