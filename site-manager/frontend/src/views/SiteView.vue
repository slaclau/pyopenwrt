<script setup lang="ts">
import { getIceServersIceServersGet } from '@/sdk';
import { onMounted, onUnmounted, ref, type Ref } from 'vue';

import { dataChannel, handleResponse, site_manager_client } from '@/client.ts';
import { useRoute } from 'vue-router';

import Controller from 'controller/App.vue'

const connected: Ref<boolean> = ref(false)
const route = useRoute();
let socket: WebSocket;
let peerConnection: RTCPeerConnection;

async function connect(url: string) {
    console.log("connecting")
    socket = new WebSocket(url) // Replace with your WebSocket URL
    console.log(socket)

    socket.onopen = () => {
        console.log("ws opened");
        socket.send(JSON.stringify({ "type": "command", "command": "connect", "site_id": route.params.site_id }));
        console.log("sent command to initiate WebRTC")
    }

    socket.onmessage = async (event) => {
        let data = JSON.parse(event.data)
        switch (data.type) {
            case "connected":
                console.log("Succesfully initiated connection")

                const configuration = (await getIceServersIceServersGet({ client: site_manager_client })).data;
                if (!configuration) return;
                peerConnection = new RTCPeerConnection(configuration);
                const dc = peerConnection.createDataChannel("http");
                dataChannel.value = dc;

                dc.addEventListener("open", (event) => {
                    console.log("dc open")
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
    }
}

onMounted(() => {
    console.log("site view mounted for", route.params.site_id)
    connect(window.origin + "/api/ws").then(() => { })
})

onUnmounted(() => {
    socket.close();
    peerConnection.close();
})
</script>

<template>
    <Controller v-loading="!connected" />
</template>