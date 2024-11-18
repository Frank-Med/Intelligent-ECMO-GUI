from kivy.app import App
from kivy.uix.gridlayout import GridLayout
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.clock import Clock
import serial
from kivy.core.window import Window
# Set the window to full screen
# Window.fullscreen = 'auto'

class MainPage(GridLayout):
    def __init__(self, **kwargs):
        super(MainPage, self).__init__(**kwargs)
        self.cols = 2
        self.spacing = 5
        self.padding = [10, 10, 10, 10]
        
        # Establish serial communication with Arduino
       # Set up serial connections
        self.serial_connection_sensor = serial.Serial('/dev/ttyACM1', baudrate=9600, timeout=1)  # Sensor connection
        self.serial_connection_blood_pump = serial.Serial('/dev/ttyACM0', baudrate=115200, timeout=1)  # Blood Pump connection

        # Initialize active module tracker and values
        self.active_module = None
        self.blood_pump_value = 0.0
        self.o2_flow_value = 0.0
        self.air_flow_value = 0.0
        self.oxygen_saturation_inlet = 0.0
        self.temperature1 = 0.0
        self.oxygen_saturation_outlet = 0.0
        self.temperature2 = 0.0
        self.oxygen_concentration = 0.0
        self.co2_outlet = 0.0  # CO2 outlet value
        self.blood_flow_rate = 0.0  # Blood flow rate
        
        # Left Column: Main Dashboard
        dashboard_layout = GridLayout(cols=1)

        # Top Row: Battery and Time
        top_row = BoxLayout(size_hint_y=None, height=50, spacing=10)
        battery_label = Label(text="[b]Battery[/b]", markup=True, size_hint_x=0.7, halign="left", valign="middle")
        time_label = Label(text="Date: 10/25/2024  Time: 4:45PM", size_hint_x=0.3, halign="right", valign="middle")
        top_row.add_widget(battery_label)
        top_row.add_widget(time_label)
        dashboard_layout.add_widget(top_row)

        # Data Panels (4x3 grid)
        self.data_grid = GridLayout(cols=3, spacing=10, padding=[0, 10, 0, 10])

        # Create individual data panels
        self.blood_pump_panel = self.create_data_panel("Rotation Speed", str(self.blood_pump_value), "RPM", "Blood Pump")
        self.o2_flow_panel = self.create_data_panel("O2 Flow Rate", f"{self.o2_flow_value:.1f}", "LPM", "O2 Flow Rate")
        self.air_flow_panel = self.create_data_panel("Air Flow", f"{self.air_flow_value:.1f}", "LPM", "Air Flow")

        # Adding panels to the data grid
        self.data_grid.add_widget(self.blood_pump_panel)
        self.data_grid.add_widget(self.create_data_panel("Blood Flow", "0", "LPM"))
        self.data_grid.add_widget(self.create_pressure_panel())  # Pressure

        self.data_grid.add_widget(self.o2_flow_panel)
        self.oxygen_concentration_panel = self.create_data_panel("O2 Concentration", "0.0", "Percent (%)")
        self.data_grid.add_widget(self.oxygen_concentration_panel)  # O2 Concentration
        self.data_grid.add_widget(self.create_o2_saturation_panel())  # O2 Saturation

        self.data_grid.add_widget(self.air_flow_panel)
        self.data_grid.add_widget(self.create_data_panel("CO2 Outlet", "0.0", "Percent (%)"))
        self.data_grid.add_widget(self.create_temperature_panel())  # Temperature

        dashboard_layout.add_widget(self.data_grid)
        
        # Bottom Row: Control Buttons (Alarm, Lock, Setup, Main Page)
        control_buttons = BoxLayout(size_hint_y=None, height=50, spacing=10)
        alarm_button = Button(text="Alarm", background_color=[1, 0, 0, 1])
        lock_button = Button(text="Lock", background_color=[0, 0, 0, 1])
        setup_button = Button(text="Setup", background_color=[0.5, 0.5, 0.5, 1])
        main_page_button = Button(text="Main Page", background_color=[0.5, 0.5, 1, 1])
        control_buttons.add_widget(alarm_button)
        control_buttons.add_widget(lock_button)
        control_buttons.add_widget(setup_button)
        control_buttons.add_widget(main_page_button)
        dashboard_layout.add_widget(control_buttons)

        # Add the dashboard layout to the main grid
        self.add_widget(dashboard_layout)

        # Right Column: Plus and Minus Buttons
        self.plus_button = Button(text="+", size_hint_y=0.5, font_size=32)
        self.plus_button.bind(on_press=self.increase_values)
        self.minus_button = Button(text="-", size_hint_y=0.5, font_size=32)
        self.minus_button.bind(on_press=self.decrease_values)

        # Layout for the control buttons
        button_layout = BoxLayout(orientation="vertical", size_hint_x=0.083)
        button_layout.add_widget(self.plus_button)
        button_layout.add_widget(self.minus_button)
        self.add_widget(button_layout)

        # Disable buttons by default
        self.plus_button.disabled = True
        self.minus_button.disabled = True

        # Schedule the update method to run periodically
        Clock.schedule_interval(self.update_from_serial, 1)  # Update every second

    def create_data_panel(self, title, value, unit, module_name=None):
        """Helper to create data panel with a title, value, and unit, optionally binding it to a module."""
        panel = BoxLayout(orientation="vertical", padding=[5, 5, 5, 5], spacing=5)
        panel.add_widget(Label(text=title, font_size=16, halign="center"))

        # Value label that will be dynamically updated
        value_label = Label(text=value, font_size=32, halign="center", bold=True)
        panel.add_widget(value_label)
        panel.add_widget(Label(text=unit, font_size=16, halign="center"))

        # If this panel corresponds to a module, bind it for touch interactions
        if module_name:
            panel.bind(on_touch_down=self.on_module_touch)
            panel.module_name = module_name
            panel.value_label = value_label

        return panel

    def create_pressure_panel(self):
        """Special panel for Inlet/Outlet pressure."""
        panel = BoxLayout(orientation="vertical", padding=[5, 5, 5, 5], spacing=5)
        panel.add_widget(Label(text="Pressure", font_size=16, halign="center"))
        pressure_layout = BoxLayout(orientation="horizontal")
        pressure_layout.add_widget(Label(text="Inlet\n0.0", halign="center"))
        pressure_layout.add_widget(Label(text="Outlet\n0.0", halign="center"))
        panel.add_widget(pressure_layout)
        panel.add_widget(Label(text="mmHg", font_size=16, halign="center"))
        return panel

    def create_o2_saturation_panel(self):
        """Special panel for Inlet/Outlet O2 Saturation."""
        panel = BoxLayout(orientation="vertical", padding=[5, 5, 5, 5], spacing=5)
        panel.add_widget(Label(text="O2 Saturation", font_size=16, halign="center"))
        saturation_layout = BoxLayout(orientation="horizontal")
        
        # Store references to the inlet and outlet labels for dynamic updating
        self.o2_inlet_label = Label(text="Inlet\n0.0", halign="center")
        self.o2_outlet_label = Label(text="Outlet\n0.0", halign="center")
        saturation_layout.add_widget(self.o2_inlet_label)
        saturation_layout.add_widget(self.o2_outlet_label)
        panel.add_widget(saturation_layout)
        panel.add_widget(Label(text="Percent (%)", font_size=16, halign="center"))
        return panel

    def create_temperature_panel(self):
        """Special panel for Inlet/Outlet Temperature."""
        panel = BoxLayout(orientation="vertical", padding=[5, 5, 5, 5], spacing=5)
        panel.add_widget(Label(text="Temperature", font_size=16, halign="center"))
        temp_layout = BoxLayout(orientation="horizontal")
        
        # Store references to the inlet and outlet temperature labels
        self.temp_inlet_label = Label(text="Inlet\n0.0", halign="center")
        self.temp_outlet_label = Label(text="Outlet\n0.0", halign="center")
        temp_layout.add_widget(self.temp_inlet_label)
        temp_layout.add_widget(self.temp_outlet_label)
        panel.add_widget(temp_layout)
        panel.add_widget(Label(text="\u00b0C", font_size=16, halign="center"))
        return panel

    def update_from_serial(self, dt):
        self.flowrate=None   
        """Read data from serial and update the labels."""
        try:
            if self.serial_connection_sensor.in_waiting > 0:
                data = self.serial_connection_sensor.readline().decode('utf-8').strip()
                values = data.split(',')

                if len(values) >= 6:  # Ensure there are enough values
                    self.oxygen_saturation_inlet = float(values[0])
                    self.temperature1 = float(values[1])
                    self.oxygen_saturation_outlet = float(values[2])
                    self.temperature2 = float(values[3])
                    self.oxygen_concentration = float(values[4])
                    self.co2_outlet = float(values[5])  # CO2 outlet
                    # Initialize flowrate variable
                    
                if self.serial_connection_blood_pump.in_waiting > 0:
                    flowrate = self.serial_connection_blood_pump.readline().decode('utf-8').strip()
                else:
                    flowrate = None   
                if flowrate is not None and flowrate.startswith('BFR:'):
                        # Split the blood_pump_value by ':' and ensure the resulting list has enough elements
                    parts = flowrate.split(':')
                     # Check if the length of parts is appropriate
                    if len(parts) > 1:  # We need at least two elements: 'BFR' and the value
                        self.blood_flow_rate = float(parts[1])  # Access the correct index (1, not 3)
                    else:
                        print("Invalid blood pump value format.")
                   
               
               # Update the labels in the Kivy app
                    self.update_labels() 
        except (ValueError, IndexError) as e:
          print(f"Error parsing data: {e}")
                   
    def update_labels(self):
        """Update all the labels in the Kivy app with the latest values."""
        self.o2_inlet_label.text = f"Inlet\n{self.oxygen_saturation_inlet:.1f}"  # O2 Saturation Inlet
        self.temp_inlet_label.text = f"Inlet\n{self.temperature1:.1f}"  # Temperature Inlet
        self.o2_outlet_label.text = f"Outlet\n{self.oxygen_saturation_outlet:.1f}"  # O2 Saturation Outlet
        self.temp_outlet_label.text = f"Outlet\n{self.temperature2:.1f}"  # Temperature Outlet
        self.oxygen_concentration_panel.children[1].text = f"{self.oxygen_concentration:.1f}"  # O2 Concentration
        self.data_grid.children[1].children[1].text = f"{self.co2_outlet:.2f}"  # CO2 Outlet
        self.data_grid.children[7].children[1].text = f"{self.blood_flow_rate:.2f}"  # Blood Flow Rat
    
    def on_module_touch(self, instance, touch):
        """Handle touch events to select a module and enable the buttons."""
        if instance.collide_point(touch.x, touch.y):
            self.active_module = instance.module_name  # Set the active module
            self.active_label = instance.value_label  # Reference the label to update
            self.show_buttons()

    def show_buttons(self):
        """Enable or disable the '+' and '-' buttons based on active module."""
        if self.active_module:
            self.plus_button.disabled = False
            self.minus_button.disabled = False
        else:
            self.plus_button.disabled = True
            self.minus_button.disabled = True

    def increase_values(self, instance):
        if  self.active_module == "Blood Pump":
            self.blood_pump_value += 50  # Example increment
            self.blood_pump_panel.children[1].text = f"{self.blood_pump_value}"  # Update Blood Pump label
            # Send the updated pump speed to the Arduino
            self.send_pump_speed_to_arduino(self.blood_pump_value)  # Send updated speed
        elif self.active_module == "Air Flow":
            self.air_flow_value += 0.5  # Example increment
            self.air_flow_panel.children[1].text = f"{self.air_flow_value:.1f}"  # Update Air Flow
            self.send_air_flow_to_arduino(self.air_flow_value)  # Send updated speed
        elif self.active_module == "O2 Flow Rate":
            self.o2_flow_value += 0.5  # Example increment
            self.o2_flow_panel.children[1].text = f"{self.o2_flow_value:.1f}"  # Update O2 Flow Rate label
            
    def decrease_values(self, instance):
         if self.active_module == "Blood Pump":
            self.blood_pump_value -= 50  # Example decrement
            self.blood_pump_panel.children[1].text = f"{self.blood_pump_value}"  # Update Blood Pump label
            self.send_pump_speed_to_arduino(self.blood_pump_value)  # Send updated speed
         elif self.active_module == "Air Flow":
          if self.air_flow_value > 0:  # Prevent negative values
            self.air_flow_value -= 0.1  # Example decrement
            self.air_flow_panel.children[1].text = f"{self.air_flow_value:.1f}"  # Update Air Flow label   
            self.send_air_flow_to_arduino(self.air_flow_value) # Send updated speed
         elif self.active_module == "O2 Flow Rate":
            self.o2_flow_value -= 0.5  # Example decrement
            self.o2_flow_panel.children[1].text = f"{self.o2_flow_value:.1f}"  # Update O2 Flow Rate label
    def send_pump_speed_to_arduino(self, pump_speed):
        try:
           # Format the pump speed command for the Arduino to control motor speed
           command = f"M:{pump_speed}\n"  # Prefix 'M:' for motor speed, Arduino will route this to 0x63
           self.serial_connection_blood_pump.write(command.encode('utf-8'))  # Send data to Arduino
           self.serial_connection_blood_pump.flush()  # Flush the output buffer to ensure the command is sent
           print(f"Sent new pump speed: {pump_speed} to MCP4725 at 0x63")  # Log for debugging
        except Exception as e:
           print(f"Error sending data to blood pump: {e}")
    
    def send_air_flow_to_arduino(self, air_flow_value):
        try:
           # Format the air flow command for the Arduino
           command = f"F:{air_flow_value}\n"  # Prefix 'F:' to specify flow rate command
           self.serial_connection_blood_pump.write(command.encode('utf-8'))  # Send flow rate data to Arduino
           self.serial_connection_blood_pump.flush()  # Flush the output buffer to ensure the command is sent
           rounded_value = round(air_flow_value, 1)  # Round to 1 decimal place
           print(f"Sent air flow value: {rounded_value} to MCP4725 at 0x62")  # Log for debugging
        except Exception as e:
           print(f"Error sending air flow data to Arduino: {e}")

    def on_stop(self):
        self.serial_connection_blood_pump.close()  # Ensure the serial connection is closed when the app stops        
        """Close serial connections when the app stops."""
        if self.serial_connection_sensor.is_open:
            self.serial_connection_sensor.close()
        if self.serial_connection_blood_pump.is_open:
            self.serial_connection_blood_pump.close()

class MyApp(App):
    def build(self):
        return MainPage()

if __name__ == "__main__":
    MyApp().run()
