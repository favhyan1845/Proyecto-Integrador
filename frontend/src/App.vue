<template>
  <div class="min-h-screen bg-slate-50 flex flex-col">
    <header class="bg-blue-600 text-white p-4 shadow-md flex justify-between items-center">
      <div class="flex items-center gap-2">
        <span class="text-2xl">🚲</span>
        <h1 class="text-xl font-bold">BiciParking Integral</h1>
      </div>
      <nav class="flex gap-4">
        <a href="#" @click.prevent="currentView = 'dashboard'" :class="{'font-bold underline': currentView === 'dashboard'}">Dashboard</a>
        <a href="#" @click.prevent="currentView = 'register'" :class="{'font-bold underline': currentView === 'register'}">Registro</a>
        <a href="#" @click.prevent="currentView = 'bikes'" :class="{'font-bold underline': currentView === 'bikes'}">Directorio QR</a>
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
                <th class="p-3 text-sm font-semibold text-slate-600">Tiempo / Costo</th>
                <th class="p-3 text-sm font-semibold text-slate-600">Carga Eléctrica</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="parking in activeParkings" :key="parking.id" class="border-b hover:bg-slate-50">
                <td class="p-3">{{ parking.bike.brand }} - {{ parking.bike.serial_number }}</td>
                <td class="p-3">{{ parking.bike.owner ? parking.bike.owner.username : 'Desconocido' }}</td>
                <td class="p-3">{{ new Date(parking.entry_time).toLocaleTimeString() }}</td>
                <td class="p-3 font-medium text-blue-700">
                  {{ calculateCurrentCost(parking.entry_time, parking.base_rate).minutes }} min / 
                  ${{ calculateCurrentCost(parking.entry_time, parking.base_rate).cost }}
                </td>
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

      <div v-if="currentView === 'register'" class="space-y-6">
        <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div class="bg-white p-6 rounded-lg shadow border border-slate-100">
            <h2 class="text-xl font-bold mb-4 text-center">Registrar Usuario</h2>
            <form @submit.prevent="registerUser" class="space-y-4">
              <div>
                <label class="block text-sm font-medium text-slate-700 mb-1">Nombre de Usuario</label>
                <input v-model="newUser.username" type="text" required class="w-full border border-slate-300 rounded p-2 outline-none focus:ring-2 focus:ring-blue-500" />
              </div>
              <div>
                <label class="block text-sm font-medium text-slate-700 mb-1">Correo Electrónico</label>
                <input v-model="newUser.email" type="email" required class="w-full border border-slate-300 rounded p-2 outline-none focus:ring-2 focus:ring-blue-500" />
              </div>
              <div>
                <label class="block text-sm font-medium text-slate-700 mb-1">Contraseña</label>
                <input v-model="newUser.password" type="password" required class="w-full border border-slate-300 rounded p-2 outline-none focus:ring-2 focus:ring-blue-500" />
              </div>
              <button type="submit" class="w-full bg-indigo-600 text-white py-2 rounded font-medium hover:bg-indigo-700 transition">Crear Usuario</button>
              <div v-if="userRegisterMessage" :class="['p-3 rounded mt-4 text-sm font-medium break-all', userRegisterIsError ? 'bg-red-100 text-red-700' : 'bg-green-100 text-green-700']">
                {{ userRegisterMessage }}
              </div>
            </form>
          </div>

          <div class="bg-white p-6 rounded-lg shadow border border-slate-100">
            <h2 class="text-xl font-bold mb-4 text-center">Registrar Nueva Bicicleta</h2>
            <form @submit.prevent="registerBike" class="space-y-4">
              <div>
                <label class="block text-sm font-medium text-slate-700 mb-1">Dueño (Usuario)</label>
                <select v-model.number="newBike.owner_id" required class="w-full border border-slate-300 rounded p-2 outline-none focus:ring-2 focus:ring-blue-500">
                  <option disabled value="">Seleccione un usuario...</option>
                  <option v-for="user in users" :key="user.id" :value="user.id">
                    {{ user.username }} ({{ user.email }})
                  </option>
                </select>
              </div>
              <div>
                <label class="block text-sm font-medium text-slate-700 mb-1">Número de Serie</label>
                <input v-model="newBike.serial_number" type="text" required class="w-full border border-slate-300 rounded p-2 outline-none focus:ring-2 focus:ring-blue-500" />
              </div>
              <div>
                <label class="block text-sm font-medium text-slate-700 mb-1">Marca</label>
                <input v-model="newBike.brand" type="text" required class="w-full border border-slate-300 rounded p-2 outline-none focus:ring-2 focus:ring-blue-500" />
              </div>
              <div>
                <label class="block text-sm font-medium text-slate-700 mb-1">Modelo</label>
                <input v-model="newBike.model" type="text" class="w-full border border-slate-300 rounded p-2 outline-none focus:ring-2 focus:ring-blue-500" />
              </div>
              <div>
                <label class="block text-sm font-medium text-slate-700 mb-1">Tipo</label>
                <select v-model="newBike.type" class="w-full border border-slate-300 rounded p-2 outline-none focus:ring-2 focus:ring-blue-500">
                  <option value="traditional">Tradicional</option>
                  <option value="electric">Eléctrica</option>
                </select>
              </div>
              <button type="submit" class="w-full bg-blue-600 text-white py-2 rounded font-medium hover:bg-blue-700 transition">Guardar Bicicleta</button>
              <div v-if="registerMessage" :class="['p-3 rounded mt-4 text-sm font-medium break-all', registerIsError ? 'bg-red-100 text-red-700' : 'bg-green-100 text-green-700']">
                {{ registerMessage }}
              </div>
            </form>
          </div>
        </div>
      </div>

      <div v-if="currentView === 'bikes'" class="space-y-6">
        <div class="bg-white p-6 rounded-lg shadow border border-slate-100">
          <div class="flex justify-between items-center mb-4">
            <h2 class="text-xl font-bold">Directorio de Bicicletas y Códigos QR</h2>
            <button @click="fetchBikes" class="text-sm bg-slate-100 px-3 py-1 rounded hover:bg-slate-200">Actualizar</button>
          </div>
          <table class="w-full text-left border-collapse">
            <thead>
              <tr class="border-b bg-slate-50">
                <th class="p-3 text-sm font-semibold text-slate-600">Propietario</th>
                <th class="p-3 text-sm font-semibold text-slate-600">Bicicleta</th>
                <th class="p-3 text-sm font-semibold text-slate-600">Tipo</th>
                <th class="p-3 text-sm font-semibold text-slate-600">Acciones</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="bike in bikes" :key="bike.id" class="border-b hover:bg-slate-50">
                <td class="p-3 font-medium">{{ getUserName(bike.owner_id) }}</td>
                <td class="p-3">{{ bike.brand }} {{ bike.model ? '- ' + bike.model : '' }} <span class="text-xs text-slate-400 block">{{ bike.serial_number }}</span></td>
                <td class="p-3">
                  <span :class="bike.type === 'electric' ? 'text-blue-600' : 'text-slate-600'">
                    {{ bike.type === 'electric' ? '⚡ Eléctrica' : 'Tradicional' }}
                  </span>
                </td>
                <td class="p-3">
                  <button @click="showQr(bike)" class="bg-indigo-100 text-indigo-700 px-3 py-1 rounded text-sm font-bold hover:bg-indigo-200 transition">Generar QR</button>
                </td>
              </tr>
              <tr v-if="bikes.length === 0">
                <td colspan="4" class="p-4 text-center text-slate-500">No hay bicicletas registradas</td>
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

    <!-- Modal QR -->
    <div v-if="selectedBikeQr" class="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4" @click.self="closeQr">
      <div class="bg-white p-6 rounded-lg max-w-sm w-full text-center shadow-xl">
        <h3 class="text-xl font-bold mb-1">Código QR de Acceso</h3>
        <p class="text-sm font-medium text-blue-600 mb-4">{{ getUserName(selectedBikeQr.owner_id) }}</p>
        
        <div class="bg-white p-4 inline-block rounded-xl border-4 border-slate-100 mb-4 shadow-sm">
          <img :src="`https://api.qrserver.com/v1/create-qr-code/?size=250x250&data=${encodeURIComponent(selectedBikeQr.qr_code)}`" alt="QR Code" class="mx-auto" />
        </div>
        
        <p class="text-slate-600 font-medium mb-1">{{ selectedBikeQr.brand }} {{ selectedBikeQr.model ? '- ' + selectedBikeQr.model : '' }}</p>
        <p class="text-xs font-mono bg-slate-100 p-2 rounded mb-4 break-all text-slate-500">{{ selectedBikeQr.qr_code }}</p>
        
        <button @click="closeQr" class="w-full bg-slate-800 text-white py-2 rounded-lg font-medium hover:bg-slate-900 transition">Cerrar</button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, watch } from 'vue';

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

const newBike = ref({
  owner_id: '',
  serial_number: '',
  brand: '',
  model: '',
  type: 'traditional'
});
const registerMessage = ref('');
const registerIsError = ref(false);

const users = ref([]);
const bikes = ref([]);
const selectedBikeQr = ref(null);
const now = ref(new Date());

const calculateCurrentCost = (entryTime, baseRate) => {
  // Asegurar formato UTC
  const entry = new Date(entryTime + (entryTime.endsWith('Z') ? '' : 'Z'));
  let diffMs = now.value - entry;
  if (diffMs < 0) diffMs = 0;
  const minutes = Math.max(1, Math.floor(diffMs / 60000));
  return {
    minutes,
    cost: (minutes * (baseRate || 10)).toFixed(2)
  };
};

const newUser = ref({
  username: '',
  email: '',
  password: ''
});
const userRegisterMessage = ref('');
const userRegisterIsError = ref(false);

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

const fetchUsers = async () => {
  try {
    const res = await fetch(`${API_URL}/users`);
    if (res.ok) {
      users.value = await res.json();
    }
  } catch (err) {
    console.error("Error fetching users:", err);
  }
};

const fetchBikes = async () => {
  try {
    const res = await fetch(`${API_URL}/bikes`);
    if (res.ok) {
      bikes.value = await res.json();
    }
  } catch (err) {
    console.error("Error fetching bikes:", err);
  }
};

const getUserName = (ownerId) => {
  const user = users.value.find(u => u.id === ownerId);
  return user ? user.username : 'Desconocido';
};

const showQr = (bike) => {
  selectedBikeQr.value = bike;
};

const closeQr = () => {
  selectedBikeQr.value = null;
};

// Cargar las bicicletas cuando se abre la vista del directorio
watch(currentView, (newVal) => {
  if (newVal === 'bikes') {
    fetchBikes();
  }
});

const registerUser = async () => {
  try {
    const res = await fetch(`${API_URL}/auth/register`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        username: newUser.value.username,
        email: newUser.value.email,
        password: newUser.value.password
      })
    });
    const data = await res.json();
    if (res.ok) {
      userRegisterMessage.value = `Usuario registrado exitosamente (ID: ${data.id})`;
      userRegisterIsError.value = false;
      newUser.value.username = '';
      newUser.value.email = '';
      newUser.value.password = '';
      await fetchUsers();
      newBike.value.owner_id = data.id;
    } else {
      userRegisterMessage.value = data.detail || 'Error al registrar usuario';
      userRegisterIsError.value = true;
    }
  } catch (err) {
    userRegisterMessage.value = 'Error de conexión';
    userRegisterIsError.value = true;
  }
  setTimeout(() => { userRegisterMessage.value = ''; }, 5000);
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
      currentView.value = 'dashboard';
    } else {
      showMessage(data.detail, true);
    }
  } catch (err) {
    showMessage("Error de conexión", true);
  }
};

const registerBike = async () => {
  try {
    const res = await fetch(`${API_URL}/bikes?owner_id=${newBike.value.owner_id}`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        serial_number: newBike.value.serial_number,
        brand: newBike.value.brand,
        model: newBike.value.model,
        type: newBike.value.type
      })
    });
    const data = await res.json();
    if (res.ok) {
      registerMessage.value = `Bicicleta registrada exitosamente. Puedes ver su QR en el Directorio.`;
      registerIsError.value = false;
      newBike.value.serial_number = '';
      newBike.value.brand = '';
      newBike.value.model = '';
      fetchDashboardData();
      fetchBikes();
    } else {
      registerMessage.value = data.detail || 'Error al registrar la bicicleta';
      registerIsError.value = true;
    }
  } catch (err) {
    registerMessage.value = 'Error de conexión';
    registerIsError.value = true;
  }
  setTimeout(() => { registerMessage.value = ''; }, 8000);
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
  fetchUsers();
  fetchBikes();
  // Polling para actualizar datos
  setInterval(() => {
    now.value = new Date();
    fetchDashboardData();
  }, 5000);
});
</script>