<template>


</template>
<script setup lang="ts">
import { ref,onMounted } from 'vue'
import axios from 'axios'

const token = localStorage.getItem('admin_access_token')
const Axios = axios.create({ baseURL: 'http://127.0.0.1:8000/api' })


</script>
