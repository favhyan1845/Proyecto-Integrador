<template>
  <div class="min-h-screen bg-slate-50 flex flex-col">
    <header class="bg-blue-600 text-white p-4 shadow-md flex justify-between items-center">
      <div class="flex items-center gap-2">
        <span class="text-2xl">🚲</span>
        <h1 class="text-xl font-bold">BiciParking Integral</h1>
      </div>
      <nav class="flex gap-4">
        <a href="#" @click.prevent="currentView = 'dashboard'" :class="{'font-bold underline': currentView === 'dashboard'}">Dashboard</a>
        <a href="#" @click.prevent="currentView = 'checkin'" :class="{'font-bold underline': currentView === 'checkin'}">Simulador QR</a>
      </nav>
    </header>

    <main class="flex-grow p-6 w-full max-w-6xl mx-auto">
      <div v-if="currentView === 'dashboard'" class="space-y-6">
        <div class="grid grid-cols-1 md:grid-cols-4 gap-4">
          <div class="bg-white p-4 rounded-lg shadow border border-slate-100">
            <h3 class="text-slate-500 text-sm font-medium">Bicicletas Registradas</h3>
            <p class="text-3xl font-bold text-slate-800">{{ stats.total_registered_bikes }}</p>
          </div>
          <div class="bg-white p-4 rounded-lg shadow border border-slate-100">
            <h3 class="text-slate-500 text-sm font-medium">Parqueos Activos</h3>
            <p class="text-3xl font-bold text-blue-600">{{ stats.active_parkings }}</p>
          </div>
          <div class="bg-white p-4 rounded-lg shadow border border-slate-100">
            <h3 class="text-slate-500 text-sm font-medium">Cargas E-Bike Activas</h3>
            <p class="text-3xl font-bold text-green-500">{{ stats.active_charges }}</p>
          </div>
          <div class="bg-white p-4 rounded-lg shadow border border-slate-100">
            <h3 class="text-slate-500 text-sm font-medium">Ingresos Totales</h3>
            <p class="text-3xl font-bold text-emerald-600">${{ stats.total_revenue }}</p>
          </div>
        </div>

        <div class="bg-white p-6 rounded-lg shadow border border-slate-100">
          <h2 class="text-lg font-bold mb-4">Parqueos Activos en Tiempo Real</h2>
          <div v-if="activeParkings.length === 0" class="text-center text-slate-500 py-8">
            No hay bicicletas en el parqueadero actualmente.
          </div>
          <table v-else class="w-full text-left border-collapse">
            <thead>
              <tr class="border-b bg-slate-50">
                <th class="p-3 text-sm font-semibold text-slate-600">Bicicleta</th>
                <th class="p-3 text-sm font-semibold text-slate-600">Dueño</th>
                <th class="p-3 text-sm font-semibold text-slate-600">Ingreso</th>
                <th class="p-3 text-sm font-semibold text-slate-600">Carga Eléctrica</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="parking in activeParkings" :key="parking.id" class="border-b hover:bg-slate-50">
                <td class="p-3">{{ parking.bike.brand }} - {{ parking.bike.serial_number }}</td>
                <td class="p-3">{{ parking.bike.owner ? parking.bike.owner.username : 'Desconocido' }}</td>
                <td class="p-3">{{ new Date(parking.entry_time).toLocaleString() }}</td>
                <td class="p-3">
                  <span v-if="parking.energy_consumption && parking.energy_consumption.status === 'active'" class="text-green-600 font-semibold text-sm flex items-center gap-1">
                    ⚡ Cargando
                  </span>
                  <span v-else class="text-slate-400 text-sm">Inactivo</span>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>

      <div v-if="currentView === 'checkin'" class="space-y-6">
        <div class="bg-white p-6 rounded-lg shadow border border-slate-100 max-w-md mx-auto">
          <h2 class="text-xl font-bold mb-4 text-center">Simulador Escáner QR</h2>
          <div class="space-y-4">
            <div>
              <label class="block text-sm font-medium text-slate-700 mb-1">Código QR</label>
              <input v-model="qrCode" type="text" placeholder="Ej: QR-BIKE-A1B2C3D4" class="w-full border border-slate-300 rounded p-2 outline-none focus:ring-2 focus:ring-blue-500" />
            </div>
            <div class="flex gap-2">
              <button @click="checkIn" class="flex-1 bg-blue-600 text-white py-2 rounded font-medium hover:bg-blue-700 transition">Entrar (Check-in)</button>
              <button @click="checkOut" class="flex-1 bg-rose-500 text-white py-2 rounded font-medium hover:bg-rose-600 transition">Salir (Check-out)</button>
            </div>
            
            <div v-if="message" :class="['p-3 rounded mt-4 text-sm font-medium', isError ? 'bg-red-100 text-red-700' : 'bg-green-100 text-green-700']">
              {{ message }}
            </div>

            <div v-if="checkoutData" class="mt-4 p-4 border border-blue-200 bg-blue-50 rounded-lg">
              <h3 class="font-bold text-blue-800 mb-2">Resumen de Cobro</h3>
              <p class="text-sm flex justify-between"><span>Tiempo:</span> <span>{{ checkoutData.duration_minutes }} min</span></p>
              <p class="text-sm flex justify-between"><span>Parqueo:</span> <span>${{ checkoutData.parking_cost }}</span></p>
              <p class="text-sm flex justify-between"><span>Carga:</span> <span>${{ checkoutData.energy_cost }}</span></p>
              <hr class="my-2 border-blue-200" />
              <p class="text-lg font-bold flex justify-between text-blue-900"><span>Total:</span> <span>${{ checkoutData.total_amount }}</span></p>
              
              <button @click="simulatePayment" class="w-full mt-4 bg-emerald-500 text-white py-2 rounded font-bold hover:bg-emerald-600 transition">
                Pagar vía Pasarela
              </button>
            </div>
          </div>
        </div>
      </div>
    </main>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue';

const API_URL = 'http://localhost:8000/api';

const currentView = ref('dashboard');
const stats = ref({
  active_parkings: 0,
  active_charges: 0,
  total_registered_bikes: 0,
  total_revenue: 0
});
const activeParkings = ref([]);

const qrCode = ref('');
const message = ref('');
const isError = ref(false);
const checkoutData = ref(null);

const fetchDashboardData = async () => {
  try {
    const statsRes = await fetch(`${API_URL}/dashboard/stats`);
    if (statsRes.ok) stats.value = await statsRes.json();

    const parkingsRes = await fetch(`${API_URL}/parking/active`);
    if (parkingsRes.ok) activeParkings.value = await parkingsRes.json();
  } catch (err) {
    console.error("Error fetching dashboard data:", err);
  }
};

const checkIn = async () => {
  if (!qrCode.value) return showMessage("Ingresa un código QR", true);
  try {
    const res = await fetch(`${API_URL}/parking/check-in`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ qr_code: qrCode.value })
    });
    const data = await res.json();
    
    if (res.ok) {
      showMessage("Ingreso registrado exitosamente");
      qrCode.value = '';
      checkoutData.value = null;
      fetchDashboardData();
    } else {
      showMessage(data.detail, true);
    }
  } catch (err) {
    showMessage("Error de conexión", true);
  }
};

const checkOut = async () => {
  if (!qrCode.value) return showMessage("Ingresa un código QR", true);
  try {
    const res = await fetch(`${API_URL}/parking/check-out`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ qr_code: qrCode.value })
    });
    const data = await res.json();
    
    if (res.ok) {
      showMessage("Salida calculada. Por favor realice el pago.");
      checkoutData.value = data;
      qrCode.value = '';
      fetchDashboardData();
    } else {
      showMessage(data.detail, true);
    }
  } catch (err) {
    showMessage("Error de conexión", true);
  }
};

const simulatePayment = async () => {
  if (!checkoutData.value) return;
  
  try {
    const res = await fetch(`${API_URL}/payments/process`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        parking_record_id: checkoutData.value.parking_record_id,
        payment_method: 'online'
      })
    });
    
    if (res.ok) {
      showMessage("¡Pago realizado con éxito! Puerta liberada.");
      checkoutData.value = null;
      fetchDashboardData();
    } else {
      const data = await res.json();
      showMessage(data.detail || "Error en el pago", true);
    }
  } catch (err) {
    showMessage("Error de conexión", true);
  }
};

const showMessage = (msg, error = false) => {
  message.value = msg;
  isError.value = error;
  setTimeout(() => { if (message.value === msg) message.value = ''; }, 4000);
};

onMounted(() => {
  fetchDashboardData();
  // Polling para actualizar datos
  setInterval(fetchDashboardData, 5000);
});
</script>
