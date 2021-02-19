import pymodbus
import time
from tkinter import *
from PIL import Image, ImageTk, ImageSequence
from pymodbus.client.sync import ModbusTcpClient as ModbusClient


class VaconModbusClient:
    def __init__(self, client):
        self.client_module = client
        self.client = None
        self.id_cache = {}

    def open(self, ip, port=502):
        self.client = self.client_module(ip, port)
        return True

    def read_by_id(self, id, extended=False):
        """
        0001 - 2000 Vacon Application IDs
        2200 - 10000 Vacon Application IDs 16bit

        20001 - 40000 Vacon Application IDs 32bit
        """
        if extended:
            ret = self.client.read_holding_registers(((id - 1) * 2) + 20000, 2)
            if isinstance(ret, pymodbus.register_read_message.ReadHoldingRegistersResponse):
                hi, lo = ret.registers
                value = (True, hi * 65536 + lo)
            else:
                value = (False, 0)
        else:
            ret = self.client.read_holding_registers(id - 1, 1)
            if isinstance(ret, pymodbus.register_read_message.ReadHoldingRegistersResponse):
                value = (True, ret.registers[0])
                self.id_cache[id] = value
            else:
                value = (False, 0)
        return value

    def write_by_id(self, id, value, extended=False):
        ret = self.client.write_register(id - 1, value)
        if isinstance(ret, pymodbus.register_write_message.WriteSingleRegisterResponse):
            value = True
            self.id_cache[id] = value
        else:
            value = False
        return value

    def write_pdi(self, values, extended=False):
        """
         2001 ... 2011 (16bit)
         2051 ... 2070 (32bit) (2051<<16+2052)

         write_registers(2000, [1,1000,2000,3000])
        """
        if extended:
            reg_16 = []
            if len(values) > 11:
                values = values[:11]
            for value in values:
                reg_16.append(value / 65536)
                reg_16.append(value % 65536)

            ret = self.client.write_registers(2050, reg_16[:10])
            if isinstance(ret, pymodbus.register_write_message.WriteMultipleRegistersResponse):
                ret = self.client.write_registers(2060, reg_16[10:])
                if isinstance(ret, pymodbus.register_write_message.WriteMultipleRegistersResponse):
                    value = (True, tuple(values))
                else:
                    value = (False, tuple())
            else:
                value = (False, tuple())

        else:
            if len(values) > 11:
                values = values[:11]
            ret = self.client.write_registers(2000, values)
            if isinstance(ret, pymodbus.register_write_message.WriteMultipleRegistersResponse):
                value = (True, tuple(values))
            else:
                value = (False, tuple())

        return value

    def control_run(self, value):
        """
        Helper function to set the drive to run state.
        """
        self.write_by_id(102, value)
        while True:
            max_percentage = 100
            for i in range(0, max_percentage, 3):
                self.write_pdi([1, 0, i * 100, 1000, 2000, 3000, 4000, 5000, 6000, 7000, 8000])

            break

    def control_stop(self):
        """
        Helper function to set the drive to stop state.
        """
        self.write_pdi([0, 0, 0, 1000, 2000, 3000, 4000, 5000, 6000, 7000, 8000])

    def status_speed(self):
        """
        Helper function to read output speed of the motor.
        """
        ret_s, SpeedOut = self.read_by_id(2105)
        return SpeedOut

    def status_frequency(self):
        """
        Helper function to read output frequency.
        """
        ret, FreqOut = self.read_by_id(2104)
        return FreqOut

    def status_current(self):
        """
        Helper function to read output current.
        """
        ret_c, CurrentOut = self.read_by_id(2106)
        return CurrentOut

    def status_torque(self):
        """
        Helper function to read output torque.
        """
        ret_t, TorqueOut = self.read_by_id(2107)
        return TorqueOut

    def status_power(self):
        """
        Helper function to read output power.
        """
        ret_p, PowerOut = self.read_by_id(2108)
        return PowerOut

    def status_DCvoltage(self):
        """
        Helper function to read output DC voltage.
        """
        ret_dc, DCOut = self.read_by_id(2110)
        return DCOut


if __name__ == '__main__':

    """
    Creating two objects for VaconModbusClient class and saving those to different variables.
    Also calling open method for those objects with unique IP addresses.
    """
    drive1 = VaconModbusClient(ModbusClient)
    ip1 = '192.168.140.179'
    drive1.open(ip1, port=502)

    drive2 = VaconModbusClient(ModbusClient)
    ip2 = '192.168.140.178'
    drive2.open(ip2, port=502)

    """
    Basic setups for GUI.
    """
    root = Tk()
    root.geometry("2100x1100")
    root.title("Vacon Drive Control App")
    root.configure(background="blue")

    """
    Options for drop menu saved in list structure and string variable for choose option.
    """
    options = ["Motor1", "Motor2", "Motor1 & Motor2", "Motor1 & Motor2 Shift"]
    clicked = StringVar()
    clicked.set(options[0])

    """
    Two variables for later use in shift_run() fuction.
    """
    var = 0
    cond = True

    """
    Function that sets necessary variables for the gif animation, and then calls functions that
    handles actual animation.
    """


    def gif():
        canvas = Canvas(root, width=400, height=400)
        canvas.place(x=400, y=200)
        sequence = [ImageTk.PhotoImage(img)
                    for img in ImageSequence.Iterator(
                Image.open(
                    "/home/pi/SpinningGif1.gif"))]
        image = canvas.create_image(200, 200, image=sequence[1])

        canvas2 = Canvas(root, width=400, height=400)
        canvas2.place(x=1100, y=200)
        sequence2 = [ImageTk.PhotoImage(img)
                     for img in ImageSequence.Iterator(
                Image.open(
                    "/home/pi/SpinningGif1.gif"))]
        image2 = canvas2.create_image(200, 200, image=sequence2[1])

        animate(canvas, image, sequence, 1)
        animate2(canvas2, image2, sequence2, 1)


    """
    Animation function for motor1 gif. Function calls itself back depending on the if statement, which is filled.
    """


    def animate(canvas, image, sequence, counter):
        canvas.itemconfig(image, image=sequence[counter])
        if drive1.status_speed() > 0 and select() == "Motor1":
            root.after(3000 // drive1.status_speed(),
                       lambda: animate(canvas, image, sequence, (counter + 1) % len(sequence)))
        if drive1.status_speed() == 0 or select() == "Motor2":
            root.after(100, lambda: animate(canvas, image, sequence, (counter) % len(sequence)))
        if drive1.status_speed() > 0 and select() == "Motor1 & Motor2":
            root.after(4000 // drive1.status_speed(),
                       lambda: animate(canvas, image, sequence, (counter + 1) % len(sequence)))
        if drive1.status_speed() > 0 and select() == "Motor1 & Motor2 Shift":
            root.after(3000 // drive1.status_speed(),
                       lambda: animate(canvas, image, sequence, (counter + 1) % len(sequence)))


    """
    Animation function for motor2 gif. Function calls itself back depending on the if statement, which is filled.
    """


    def animate2(canvas2, image2, sequence2, counter2):
        canvas2.itemconfig(image2, image=sequence2[counter2])
        if drive2.status_speed() > 0 and select() == "Motor2":
            root.after(7000 // drive2.status_speed(),
                       lambda: animate2(canvas2, image2, sequence2, (counter2 + 1) % len(sequence2)))
        if drive2.status_speed() == 0 or select() == "Motor1":
            root.after(100, lambda: animate2(canvas2, image2, sequence2, (counter2) % len(sequence2)))
        if drive2.status_speed() > 0 and select() == "Motor1 & Motor2":
            root.after(12000 // drive2.status_speed(),
                       lambda: animate2(canvas2, image2, sequence2, (counter2 + 1) % len(sequence2)))
        if drive2.status_speed() > 0 and select() == "Motor1 & Motor2 Shift":
            root.after(12000 // drive2.status_speed(),
                       lambda: animate2(canvas2, image2, sequence2, (counter2 + 1) % len(sequence2)))


    """
    Function which saves incoming values from the drive1 to variables, and then configures them. Function calls itself back after every 1000 msec.
    """


    def read1():
        speed = drive1.status_speed()
        frequency = drive1.status_frequency()
        current = drive1.status_current()
        DCvoltage = drive1.status_DCvoltage()
        torque = drive1.status_torque()
        power = drive1.status_power()
        label1.configure(text=str(speed))
        label2.configure(text=str(frequency))
        label3.configure(text=str(current))
        label4.configure(text=str(DCvoltage))
        label5.configure(text=str(torque))
        label6.configure(text=str(power))
        root.after(1000, read1)


    """
    Function which saves incoming values from the drive2 to variables, and then configures them. Function calls itself back after every 1000 msec.
    """


    def read2():
        speed2 = drive2.status_speed()
        frequency2 = drive2.status_frequency()
        current2 = drive2.status_current()
        DCvoltage2 = drive2.status_DCvoltage()
        torque2 = drive2.status_torque()
        power2 = drive2.status_power()
        label1_2.configure(text=str(speed2))
        label2_2.configure(text=str(frequency2))
        label3_2.configure(text=str(current2))
        label4_2.configure(text=str(DCvoltage2))
        label5_2.configure(text=str(torque2))
        label6_2.configure(text=str(power2))
        root.after(1000, read2)


    """
    Function for the event when the Start/Set button has been pressed.
    """


    def click_start():
        if select() == "Motor1":
            drive1.control_run(freq_slider())
            drive2.control_stop()
            read1()
        elif select() == "Motor2":
            drive2.control_run(freq_slider())
            drive1.control_stop()
            read2()
        elif select() == "Motor1 & Motor2":
            drive1.control_run(freq_slider())
            drive2.control_run(freq_slider())
            read1()
            read2()
        elif select() == "Motor1 & Motor2 Shift":
            read1()
            read2()
            shift_run()

        """
        Function contains if staments for all running options.
        """


    """
    Function for sequence logic when the "Motor1 & Motor2 Shift" option has been chosen.
    """


    def shift_run():
        global var
        """
        Int variable that starts counting when the drive1 stops and the drive2 starts.
        """
        global cond
        """
        Boolean variable for checking that program is not in stop state.
        """
        if var == 0:
            drive1.control_run(freq_slider())
            """
            Sequence starting with the drive1.
            """
        if drive1.status_frequency() > (freq_slider() - 27) or var > 0 and var < 26:
            drive1.control_stop()
            drive2.control_run(freq_slider())
            var = var + 1
            """
            When the drive has reach the setted frequency it stop and the drive2 starts.
            Var variable counting starts also.
            """
        if var == 26:
            drive2.control_stop()
            var = 0
            """
            When the var variable counting has reached 26 the drive2 stops and sequence starts again with the drive1
            by setting the var variable to 0.
            """
        if cond == False or select() != "Motor1 & Motor2 Shift":
            drive1.control_stop()
            drive2.control_stop()
            cond = True
            var = 0
            stop()
            """
            Checking sequence condtions.
            """
        if var < 26:
            root.after(2000, shift_run)
            """
            Function calls itself back when the var variable is under 26.
            """


    """
    Function for the event when the Stop button has been pressed.
    """


    def click_stop():
        drive1.control_stop()
        drive2.control_stop()
        global cond
        cond = False


    """
    Function for the event when the application is closing.
    """


    def quit_program():
        drive1.control_stop()
        drive2.control_stop()
        root.destroy()


    """
    Function which takes slider widget value and returns it.
    """


    def freq_slider():
        value = slider.get()
        return value


    """
    Function which takes drop menu value and returns it. This function stops
    motor also if another option has been chosen.
    """


    def select():
        value = clicked.get()
        if value == "Motor1" or value == "Motor1 & Motor2 Shift" and var == 0:
            drive2.control_stop()
        if value == "Motor2" or value == "Motor1 & Motor2 Shift" and var != 0:
            drive1.control_stop()
        return value


    """
    Label and widget variables.
    """
    label1 = Label(root, text="", bg="blue", fg="white")
    label_s = Label(root, text="Motor speed (rpm) = ", bg="blue", fg="white")
    label1.place(x=643, y=610)
    label_s.place(x=400, y=610)
    label1.config(font=("Courier", 15))
    label_s.config(font=("Courier", 15))

    label2 = Label(root, text="", bg="blue", fg="white")
    label_f = Label(root, text="Output frequency (Hz/100) = ", bg="blue", fg="white")
    label2.place(x=738, y=630)
    label_f.place(x=400, y=630)
    label2.config(font=("Courier", 15))
    label_f.config(font=("Courier", 15))

    label3 = Label(root, text="", bg="blue", fg="white")
    label_c = Label(root, text="Motor current (A/100) = ", bg="blue", fg="white")
    label3.place(x=690, y=650)
    label_c.place(x=400, y=650)
    label3.config(font=("Courier", 15))
    label_c.config(font=("Courier", 15))

    label4 = Label(root, text="", bg="blue", fg="white")
    label_DC = Label(root, text="DC-link voltage (V) = ", bg="blue", fg="white")
    label4.place(x=655, y=714)
    label_DC.place(x=400, y=714)
    label4.config(font=("Courier", 15))
    label_DC.config(font=("Courier", 15))

    label5 = Label(root, text="", bg="blue", fg="white")
    label_t = Label(root, text="Motor torque (0.1%) = ", bg="blue", fg="white")
    label5.place(x=668, y=670)
    label_t.place(x=400, y=670)
    label5.config(font=("Courier", 15))
    label_t.config(font=("Courier", 15))

    label6 = Label(root, text="", bg="blue", fg="white")
    label_p = Label(root, text="Motor power (0.1%) = ", bg="blue", fg="white")
    label6.place(x=653, y=690)
    label_p.place(x=400, y=690)
    label6.config(font=("Courier", 15))
    label_p.config(font=("Courier", 15))

    label1_2 = Label(root, text="", bg="blue", fg="white")
    label_s_2 = Label(root, text="Motor speed (rpm) = ", bg="blue", fg="white")
    label1_2.place(x=1343, y=610)
    label_s_2.place(x=1100, y=610)
    label1_2.config(font=("Courier", 15))
    label_s_2.config(font=("Courier", 15))

    label2_2 = Label(root, text="", bg="blue", fg="white")
    label_f_2 = Label(root, text="Output frequency (Hz/100) = ", bg="blue", fg="white")
    label2_2.place(x=1438, y=630)
    label_f_2.place(x=1100, y=630)
    label2_2.config(font=("Courier", 15))
    label_f_2.config(font=("Courier", 15))

    label3_2 = Label(root, text="", bg="blue", fg="white")
    label_c_2 = Label(root, text="Motor current (A/100) = ", bg="blue", fg="white")
    label3_2.place(x=1390, y=650)
    label_c_2.place(x=1100, y=650)
    label3_2.config(font=("Courier", 15))
    label_c_2.config(font=("Courier", 15))

    label4_2 = Label(root, text="", bg="blue", fg="white")
    label_DC_2 = Label(root, text="DC-link voltage (V) = ", bg="blue", fg="white")
    label4_2.place(x=1355, y=714)
    label_DC_2.place(x=1100, y=714)
    label4_2.config(font=("Courier", 15))
    label_DC_2.config(font=("Courier", 15))

    label5_2 = Label(root, text="", bg="blue", fg="white")
    label_t_2 = Label(root, text="Motor torque (0.1%) = ", bg="blue", fg="white")
    label5_2.place(x=1368, y=670)
    label_t_2.place(x=1100, y=670)
    label5_2.config(font=("Courier", 15))
    label_t_2.config(font=("Courier", 15))

    label6_2 = Label(root, text="", bg="blue", fg="white")
    label_p_2 = Label(root, text="Motor power (0.1%) = ", bg="blue", fg="white")
    label6_2.place(x=1353, y=690)
    label_p_2.place(x=1100, y=690)
    label6_2.config(font=("Courier", 15))
    label_p_2.config(font=("Courier", 15))

    label7 = Label(root, text="Max frequency control (0-2500Hz/100 Motor 1 & 0-1500Hz/100 Motor 2)", bg="blue",
                   fg="white")
    label7.place(x=700, y=80)

    motor1_label = Label(root, text="MOTOR 1", bg="blue", fg="white")
    motor1_label.config(font=("Courier", 20))
    motor1_label.place(x=550, y=160)

    motor1_label_2 = Label(root, text="MOTOR 2", bg="blue", fg="white")
    motor1_label_2.config(font=("Courier", 20))
    motor1_label_2.place(x=1250, y=160)

    slider = Scale(root, from_=0, to=2526, orient=HORIZONTAL, showvalue=0, length=200)
    button_start = Button(root, text="Start/Set", command=click_start, fg="white", bg="green")
    button_stop = Button(root, text="Stop", command=click_stop, fg="white", bg="red")
    drop_menu = OptionMenu(root, clicked, *options)

    slider.place(x=838, y=50)
    button_start.place(x=927, y=20)
    button_stop.place(x=870, y=20)
    drop_menu.place(x=900, y=110)

    gif()
    """
    Gif function call out.
    """
    root.protocol("WM_DELETE_WINDOW", quit_program)
    """
    GUI obeject method for deleting running program when quit_program() function is called.
    """
    root.mainloop()
    """
    The main loop function call out for GUI.
    """

