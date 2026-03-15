const map = L.map("map", { 
  zoomControl: false,
  worldCopyJump: false,
  minZoom: 2,
  maxBounds: [[-85, -180], [85, 180]]
}).setView([24.9, -80.8], 9);

L.control.zoom({ position: "bottomright" }).addTo(map);
L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
  attribution: "&copy; OpenStreetMap contributors",
  noWrap: true,
  bounds: [[-85, -180], [85, 180]]
}).addTo(map);

const state = {
  user: null,
  sites: [],
  selectedSiteId: null,
  markers: new Map(),
  isInitialLoad: true,
};

const elements = {
  siteCount: document.getElementById("siteCount"),
  regionCount: document.getElementById("regionCount"),
  contributorCount: document.getElementById("contributorCount"),
  siteList: document.getElementById("siteList"),
  siteForm: document.getElementById("siteForm"),
  editorMode: document.getElementById("editorMode"),
  editorTitle: document.getElementById("editorTitle"),
  submitButton: document.getElementById("submitButton"),
  resetButton: document.getElementById("resetButton"),
  formStatus: document.getElementById("formStatus"),
  focusTitle: document.getElementById("focusTitle"),
  focusMeta: document.getElementById("focusMeta"),
};

const fieldIds = ["name", "region", "lat", "lng", "difficulty", "depth_ft", "visibility_ft", "notes"];
const formFields = Object.fromEntries(fieldIds.map((id) => [id, document.getElementById(id)]));

function setFormStatus(message = "", kind = "") {
  elements.formStatus.textContent = message;
  elements.formStatus.className = `status ${kind}`.trim();
}

function contributorLabel(actor) {
  return actor?.display_name || actor?.email || actor?.identifier || actor?.sub || "Unknown";
}

function popupMarkup(site) {
  return `
    <strong>${site.name}</strong><br />
    ${site.region}<br />
    ${site.difficulty} · ${site.depth_ft} ft depth · ${site.visibility_ft} ft visibility<br />
    Added by ${contributorLabel(site.added_by)}<br />
    ${site.notes}
  `;
}

function syncStats() {
  elements.siteCount.textContent = state.sites.length;
  elements.regionCount.textContent = new Set(state.sites.map((site) => site.region)).size;
  elements.contributorCount.textContent = new Set(state.sites.map((site) => contributorLabel(site.added_by))).size;
}

function updateFocus(site) {
  if (!site) {
    elements.focusTitle.textContent = "No site selected";
    elements.focusMeta.textContent = "Select a marker or site card to inspect details.";
    return;
  }

  elements.focusTitle.textContent = site.name;
  elements.focusMeta.textContent = `${site.region} · ${site.difficulty} · added by ${contributorLabel(site.added_by)}`;
}

function syncEditorTitle() {
  const isUpdateMode = elements.editorMode.value === "update";
  elements.editorTitle.textContent = isUpdateMode ? "Update Dive Site" : "Add Dive Site";
  elements.submitButton.textContent = isUpdateMode ? "Update site" : "Save site";
}

function resetForm(keepStatus = false) {
  elements.siteForm.reset();
  formFields.difficulty.value = "Open Water";
  elements.editorMode.value = "create";
  state.selectedSiteId = null;
  syncEditorTitle();
  updateFocus(null);
  renderSiteList();
  if (!keepStatus) {
    setFormStatus();
  }
}

function populateForm(site) {
  fieldIds.forEach((id) => {
    formFields[id].value = site[id];
  });
  elements.editorMode.value = "update";
  state.selectedSiteId = site.id;
  syncEditorTitle();
}

function selectSite(siteId, focusMap = true) {
  state.selectedSiteId = siteId;
  const site = state.sites.find((entry) => entry.id === siteId) || null;
  renderSiteList();
  updateFocus(site);
  if (site) {
    populateForm(site);
    if (focusMap) {
      map.flyTo([site.lat, site.lng], Math.max(map.getZoom(), 10), { duration: 0.8 });
      state.markers.get(site.id)?.openPopup();
    }
  }
}

function renderSiteList() {
  elements.siteList.innerHTML = "";
  state.sites.forEach((site) => {
    const button = document.createElement("button");
    button.type = "button";
    button.className = `site-item${site.id === state.selectedSiteId ? " active" : ""}`;
    button.innerHTML = `
      <strong>${site.name}</strong>
      <span>${site.region} · ${site.difficulty}</span>
      <span>Added by ${contributorLabel(site.added_by)}</span>
    `;
    button.addEventListener("click", () => selectSite(site.id));
    elements.siteList.appendChild(button);
  });
}

function renderMarkers() {
  for (const marker of state.markers.values()) {
    marker.remove();
  }
  state.markers.clear();

  const bounds = [];
  state.sites.forEach((site) => {
    const marker = L.marker([site.lat, site.lng]).addTo(map).bindPopup(popupMarkup(site));
    marker.on("click", () => selectSite(site.id, false));
    state.markers.set(site.id, marker);
    bounds.push([site.lat, site.lng]);
  });

  if (bounds.length && state.isInitialLoad) {
    map.fitBounds(bounds, { padding: [70, 70], maxZoom: 10 });
    state.isInitialLoad = false;
  }
}

async function loadSites() {
  const response = await fetch("/api/dive-sites");
  const sites = await response.json();
  state.sites = sites;
  syncStats();
  renderSiteList();
  renderMarkers();
  if (state.selectedSiteId) {
    const stillExists = state.sites.some((site) => site.id === state.selectedSiteId);
    if (stillExists) {
      updateFocus(state.sites.find((site) => site.id === state.selectedSiteId));
    } else {
      resetForm(true);
    }
  }
}

async function checkAuth() {
  const response = await fetch("/api/user");
  const user = await response.json();
  state.user = user;
  
  // Disable submit button if not logged in
  if (!user || user.error) {
    elements.submitButton.disabled = true;
    state.user = null;
  } else {
    elements.submitButton.disabled = false;
  }
}

async function submitSite(event) {
  event.preventDefault();
  setFormStatus();

  const payload = {
    name: formFields.name.value.trim(),
    region: formFields.region.value.trim(),
    lat: Number(formFields.lat.value),
    lng: Number(formFields.lng.value),
    difficulty: formFields.difficulty.value,
    depth_ft: Number(formFields.depth_ft.value),
    visibility_ft: Number(formFields.visibility_ft.value),
    notes: formFields.notes.value.trim(),
  };

  try {
    const isUpdate = elements.editorMode.value === "update";
    if (isUpdate && !state.selectedSiteId) {
      throw new Error("Choose a dive site before using update mode.");
    }

    const endpoint = isUpdate ? `/api/dive-sites/${state.selectedSiteId}` : "/api/dive-sites";
    const method = isUpdate ? "PUT" : "POST";
    const response = await fetch(endpoint, {
      method,
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
    const result = await response.json();
    if (!response.ok) {
      throw new Error(result.error || "Request failed.");
    }

    await loadSites();
    selectSite(result.id);
    setFormStatus(isUpdate ? "Dive site updated." : "Dive site added.", "success");
  } catch (error) {
    setFormStatus(error.message, "error");
  }
}

elements.siteForm.addEventListener("submit", submitSite);
elements.editorMode.addEventListener("change", syncEditorTitle);
elements.resetButton.addEventListener("click", () => resetForm());

syncEditorTitle();
await checkAuth();
await loadSites();
