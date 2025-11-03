import requests
import json
# "id":1,"method":"EM1.GetStatus","params":{"id":0}}

shelly = "http://192.168.1.162/rpc"


#  r = requests.get("http://192.168.1.51/relay/0?turn=on")
shelly_socket = "http://192.168.1.51/relay/0?turn="

def socket_off():
  combined = shelly_socket + "off"
  print(combined)
  r = requests.get(combined)
  print(r)

def socket_on():
  combined = shelly_socket + "on"
  r = requests.get(combined)



def read_meter():
  pass


if __name__ == '__main__':

#url = "http://localhost:8080"

  data = {'id': '1',
          'method': 'EM1.GetStatus',
          'params': {'id':'0'}
         }
  headers = {'Content-type': 'application/json', 'Accept': 'text/plain'}
  r = requests.post(shelly, data=json.dumps(data), headers=headers)
  y = json.loads(r.text)

  act_power_value = y["result"]["act_power"]
  #print(type(act_power_value))
  print(act_power_value)
  if act_power_value < -30:
    print("Atentie, energie injectata in retea, pornire consumatori")
    socket_on()
