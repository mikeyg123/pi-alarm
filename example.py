import sc16is7x0 as sc 
import keypad as key

x = sc.Uart(0x48, 14745600) 
x.setup(1200, 8, "O", 1, "K")  

k = new key.Keypad(x)
k.write("hello world")

