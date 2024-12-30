## WITRN Protocol

Works with WITRN C4/C4L/C5, A2, U3, C4 series

## Protocol Layer

- USB HID

## Packet Structures

The **[USBPac](#USBPac)** is sent at a fixed rate as long as the meter is connected to the USB. the sampling rate depends on the Host's rotation rate rather than the meter's **[USBPac](#USBPac)** sending rate

---

### USBPac

The most basic packet structure, transmitted via HID Data. Each packet starts with a fixed "start" and "head"

```c#
struct USBPac {
	byte start; // 0xFF
	byte head; 	// 0x55
	byte idx1;
	byte idx2;
	byte needAck;
	// USBPac.<free>e__FixedBuffer free; // bytes[3]
	bytes[3] free;
	USBSPac pac;
	byte verify;
}
```

| start `byte` | head `byte` | idx1 `byte` | idx2 `byte` | needAck `byte` | free `3 bytes` | pac `55 bytes` | verify `byte` |
| :----------: | :---------: | :---------: | :---------: | :------------: | :------------: | :------------: | :-----------: |
|      FF      |     55      |     Any     |     Any     |      Any       |      Any       |   Structure    |      Any      |

- **start**

	Fixed, 0xFF

	```c#
	p->start = byte.MaxValue;
	```

- **head**

	Fixed, 0x55

	```c#
	p->head = 85;
	```

- **idx1**

	Seconds part of the timing

	```c#
	p->idx1 = (byte)(time / 1000U);
	```

- **idx2**

	Millisecond part of the timing

	```c#
	p->idx2 = (byte)(time % 1000U);
	```

- **needAck**

	When this request needs to be replied to. For example, if host requests the version or serial number of a meter, it will get the data in the response

	Specify by the flag bit

	```c#
	if (bneedAck) {
		p->needAck = (byte)(time / 30U | 128U);
	} else {
		p->needAck = (byte)(time / 30U & 127U);
	}
	```

	If a reply is required, it will follow a read process after sending the data

	```c#
	if (this.SendPac(&pac, 1000) == sizeof(USBPac)) {
		if (bNeedAck) {
			Mem.memset((void*)(&pac), 0, sizeof(USBPac));
			if (!this.beInAutoReadMode) {
				if (this.ReadPac(&pac, timeout) == sizeof(USBPac) && Transef.usb_decodeUsbPac(&pac) && pac.pac.command == command) {
					Mem.memcpy(prev, (void*)(&pac.pac.buf.FixedElementField), (int)readSize);
					res = true;
				}
			}
			else if (this.ReadAsyn(&pac, command, timeout, timeStart) == sizeof(USBPac)) {
				Mem.memcpy(prev, (void*)(&pac.pac.buf.FixedElementField), (int)readSize);
				res = true;
			}
		}
		else {
			res = true;
		}
	}
	```

- **free**

  Some time-related data. No specific use is identified

  ```c#
  p->free.FixedElementField = (byte)(time / 100U);
  *(ref p->free.FixedElementField + 1) = (byte)(time % 100U);
  *(ref p->free.FixedElementField + 2) = (byte)(time / 80U);
  ```

- **pac**

  Structure, see **[USBSPac](#USBSPac)**. Valid data section

- **verify**

  Check digits

  ```c#
  public unsafe static byte getUsbPacSum(USBPac* p) {
  	return Transef.getUsbSPacSum(&p->pac) + p->start + p->head + p->idx1 + p->idx2 + p->free.FixedElementField + *(ref p->free.FixedElementField + 1) + *(ref p->free.FixedElementField + 2) + p->needAck;
  }
  ```

---

### USBSPac

**pac** field of **[USBPac](#USBPac)**. Used for sending commands from the host side to the meter side, or reporting data from the meter side to the host

```c#
struct USBSPac {
	byte command;
	byte length;
	// USBSPac.<buf>e__FixedBuffer buf; // bytes[52]
	bytes[52] buf; // MeterData
	byte verify;
}
```

| command `byte` | length `byte` | buf `52 bytes` | verify `byte` |
| :------------: | :-----------: | :------------: | :-----------: |
|      Any       |      Any      |   Structure    |      Any      |

- **command**

	No specific use is identified

- **length**

	**buf** Length

- **buf**

	Data to be sent by the host to the meter side, or data reported by the meter side

	- Data sent from the host to the meter side

		Known usage cases are to get the table firmware version, serial number

	- Data reported by the meter side

		Structure，see **[MeterData](#MeterData)**。Valid data section

- **verify**

	Check digits

	```c#
	public unsafe static byte getUsbSPacSum(USBSPac* p) {
		byte verify = 0;
		for (int idx = 0; idx < sizeof(USBSPac) - 1; idx++) {
			verify += *(byte*)(p + idx / sizeof(USBSPac));
		}
		return verify;
	}
	```

---

### MeterData

**buf** field of **[USBSPac](#USBSPac)**. Data reported by the meter side

```c#
struct MeterData {
	byte OffPer;
	byte OffHour;
	ushort RecmA;
	float Ah;
	float Wh;
	uint RecTime;
	uint RunTime;
	float dp;
	float dm;
	float TempIn;
	float TempOut;
	float vol;
	float cur;
	byte RecGrp;
	// public MeterData.<reseverd>e__FixedBuffer reseverd; // bytes[7]
	bytes[7] reseverd;
}
```

| OffPer `byte` | OffHour `byte` | RecmA `ushort` | Ah `float` | Wh `float` | RecTime `uint` | RunTime `uint` | dp `float` | dm `float` | TempIn `float` | TempOut `float` | vol `float` | cur  `float` | RecGrp `byte` | reseverd `7 byte` |
| :-----------: | :------------: | :------------: | :--------: | :--------: | :------------: | :------------: | :--------: | :--------: | :------------: | :-------------: | :---------: | :----------: | :-----------: | :---------------: |
|      Any      |      Any       |      Any       |    Any     |    Any     |      Any       |      Any       |    Any     |    Any     |      Any       |       Any       |     Any     |     Any      |      Any      |        Any        |

- **OffPer**

	No specific use is identified

- **OffHour**

	No specific use is identified

- **RecmA**

	No specific use is identified

- **Ah**

	Recorded capacity since the beginning

- **Wh**

	Recorded energy since the beginning

- **RecTime**

	Time elapsed since start of recording

- **RunTime**

	Time elapsed since start of running

- **dp**

	Data Positive (D+) Voltage

- **dm**

	Data Negative (D-) Voltage

- **TempIn**

	Temperature of input direction

- **TempOut**

	Temperature of output direction

- **vol**

	Real-time voltage

- **cur**

	Real-time current

- **RecGrp**

	Current data group

- **reseverd**

	Unused

---

## Demo

[demo.py](./demo.py)

