<script setup lang="ts">
import { onMounted } from 'vue';


onMounted(() => {
  console.log("mounted");

  let socket = new WebSocket('ws://100.64.0.7:8001/ws') // Replace with your WebSocket URL
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
    peerConnection = new RTCPeerConnection(configuration);
    const dc = peerConnection.createDataChannel("http");
    dc.addEventListener("open", () => {
      console.log("Established data channel")
      setInterval(() => {
        dc.send("hello, this is the browser");
      }, 1000)
    })
    dc.addEventListener("message", (message) => {
      console.log(`received ${message.data} from the remote site`)
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
  }

  socket.onmessage = (event) => {
    let data = JSON.parse(event.data)
    switch (data.type) {
      case "answer":
        peerConnection.setRemoteDescription(new RTCSessionDescription(data.answer));

        break;
      default:
        console.warn("unknown ws message type", data.type)
    }
  }

  socket.onclose = () => {
    console.warn("ws closed");
  }
})
</script>

<template>
  <h1>You did it!</h1>
  <p>
    Visit <a href="https://vuejs.org/" target="_blank" rel="noopener">vuejs.org</a> to read the
    documentation
  </p>
</template>

<style scoped></style>
