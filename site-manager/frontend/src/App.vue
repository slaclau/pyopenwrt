<script setup lang="ts">
import { onMounted, ref, type Ref } from 'vue';

import Controller from 'controller/App.vue'
import { dataChannel, handleResponse } from './client.ts';
import type { Status } from 'controller/sdk/types.gen.ts';

const status: Ref<string | Status> = ref("Waiting for status");
const connected: Ref<boolean> = ref(false)

function connect(url: string) {
  let socket = new WebSocket(url) // Replace with your WebSocket URL
  let peerConnection: RTCPeerConnection;
  const configuration = {
    iceServers: [
      {
        urls: "stun:stun.relay.metered.ca:80",
      },
      {
        urls: "turn:global.relay.metered.ca:80",
        username: "d87da67fe0fe83c87d7f00ab",
        credential: "E2B6csPO3iJL2ocH",
      },
      {
        urls: "turn:global.relay.metered.ca:80?transport=tcp",
        username: "d87da67fe0fe83c87d7f00ab",
        credential: "E2B6csPO3iJL2ocH",
      },
      {
        urls: "turn:global.relay.metered.ca:443",
        username: "d87da67fe0fe83c87d7f00ab",
        credential: "E2B6csPO3iJL2ocH",
      },
      {
        urls: "turns:global.relay.metered.ca:443?transport=tcp",
        username: "d87da67fe0fe83c87d7f00ab",
        credential: "E2B6csPO3iJL2ocH",
      },
    ],
  }

  socket.onopen = () => {
    console.log("ws opened");
    socket.send(JSON.stringify({ "type": "command", "command": "connect" }));
  }

  socket.onmessage = (event) => {
    let data = JSON.parse(event.data)
    switch (data.type) {
      case "connected":
        console.log("Succesfully initiated connection")
        peerConnection = new RTCPeerConnection(configuration);
        const dc = peerConnection.createDataChannel("http");
        dataChannel.value = dc;

        dc.addEventListener("open", (event) => {
          connected.value = true;
        })

        dc.addEventListener("message", (message) => {
          console.debug(`received ${message} from the remote site`)
          const data = JSON.parse(message.data);
          switch (data.type) {
            case "response":
              handleResponse(data)
              break;
            default:
              console.warn("unexpected data channel message", data)
          }
        })

        peerConnection.addEventListener("icecandidate", (event) => {
          console.debug("Gathered new ICE candidate", event.candidate)
          socket.send(JSON.stringify({ "type": "ice-candidate", "ice-candidate": event.candidate }))
        })

        peerConnection.addEventListener("icegatheringstatechange", () => {
          console.log("ICE Gathering state is", peerConnection.iceGatheringState)
        })

        peerConnection.createOffer().then((offer) => {
          peerConnection.setLocalDescription(offer);
          socket.send(JSON.stringify({ "type": "offer", "offer": offer }))
        })
        break;

      case "answer":
        peerConnection.setRemoteDescription(new RTCSessionDescription(data.answer));
        break;

      case "error":
        console.error(data)
        connect(url);
        break;

      default:
        console.warn("unknown ws message type", data.type)
    }
  }

  socket.onclose = () => {
    console.warn("ws closed");
    connect(url);
  }
}

onMounted(() => {
  console.log("mounted");

  connect('ws://100.64.0.7:8001/ws')
})
</script>

<template>
  <Controller v-if="connected" />
  <div v-else>
    Waiting for data channel to be established
  </div>
</template>

<style scoped></style>
