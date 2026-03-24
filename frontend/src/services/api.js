// api.js

import axios from "axios"

const BASE = "http://localhost:8000/api"

const api = axios.create({
  baseURL: BASE,
  timeout: 30000,
  headers: { "Content-Type": "application/json" },
})

export const scanURL = async (url) => {
  const { data } = await api.post("/scan", { url })
  return data
}

export const scanURLOnly = async (url) => {
  const { data } = await api.post("/analyze-url", { url })
  return data
}

export const scanVisual = async (url) => {
  const { data } = await api.post("/analyze-visual", { url })
  return data
}

export const scanPayment = async (url) => {
  const { data } = await api.post("/analyze-payment", { url })
  return data
}

export default api