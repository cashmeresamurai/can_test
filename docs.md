- receive bytes

```bash
sudo python3 /home/nix/Documents/GitHub/can_test/programming_examples/CAN/python/dev_tester/vscantester.py -r -b 100000 /dev/ttyUSB0
```

- send bytes continiously
```bash
sudo python3 /home/nix/Documents/GitHub/can_test/programming_examples/CAN/python/dev_tester/vscantester.py -t same -b 100000 /dev/ttyUSB1
```

