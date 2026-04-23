// filepath: frontend/src/components/GameMap.jsx
import { useEffect, useMemo, useRef, useState } from "react";
import Map, { Source, Layer, NavigationControl } from "react-map-gl/maplibre";
import "maplibre-gl/dist/maplibre-gl.css";

const MINSK_CENTER = { longitude: 27.5615, latitude: 53.9045 };
const INITIAL_ZOOM = 13;
const MAP_STYLE = "https://tiles.openfreemap.org/styles/liberty";

const CATEGORY_COLORS = {
  restaurant: "#E07A5F",
  grocery: "#81B29A",
  fuel: "#F2CC8F",
  other: "#3D5A80",
};

function hexToGeoJSON(hexes) {
  return {
    type: "FeatureCollection",
    features: hexes.map((h) => ({
      type: "Feature",
      properties: { hex_id: h.hex_id, is_unlocked: !!h.is_unlocked },
      geometry: {
        type: "Polygon",
        coordinates: [
          h.vertices.map((v) => [v[1], v[0]]).concat([[h.vertices[0][1], h.vertices[0][0]]]),
        ],
      },
    })),
  };
}

function pointsToGeoJSON(items, keyExtras = {}) {
  return {
    type: "FeatureCollection",
    features: (items || []).map((p) => ({
      type: "Feature",
      properties: {
        partner_id: p.id ?? p.partner_id ?? null,
        name: p.name ?? p.partner_name,
        category: p.category,
        cashback: p.cashback_percent,
        pending_id: p.pending_id ?? null,
        ...keyExtras,
      },
      geometry: { type: "Point", coordinates: [p.lng, p.lat] },
    })),
  };
}

export default function GameMap({ hexes, partners, pending, onConsume, onSelectPartner }) {
  const [pulse, setPulse] = useState(8);
  const [selectedId, setSelectedId] = useState(null);
  const mapRef = useRef(null);

  const hexGeoJSON = useMemo(() => hexToGeoJSON(hexes), [hexes]);
  const partnersGeoJSON = useMemo(() => pointsToGeoJSON(partners), [partners]);
  const pendingGeoJSON = useMemo(() => pointsToGeoJSON(pending), [pending]);

  useEffect(() => {
    let t = 0;
    const id = setInterval(() => {
      t += 1;
      setPulse(10 + Math.sin(t / 3) * 4);
    }, 80);
    return () => clearInterval(id);
  }, []);

  return (
    <Map
      ref={mapRef}
      initialViewState={{
        longitude: MINSK_CENTER.longitude,
        latitude: MINSK_CENTER.latitude,
        zoom: INITIAL_ZOOM,
      }}
      mapStyle={MAP_STYLE}
      style={{ width: "100%", height: "100%" }}
      interactiveLayerIds={["partners-circle", "pending-circle"]}
      onClick={(e) => {
        const f = e.features?.[0];
        if (!f) return;
        if (f.layer.id === "pending-circle") {
          if (onConsume && f.properties.pending_id) {
            onConsume(f.properties.pending_id);
          }
        } else if (f.layer.id === "partners-circle") {
          setSelectedId(f.properties.partner_id);
          const [lng, lat] = f.geometry.coordinates;
          mapRef.current?.flyTo({ center: [lng, lat], zoom: Math.max(mapRef.current.getZoom(), 14), duration: 600 });
          if (onSelectPartner) {
            onSelectPartner({ id: f.properties.partner_id, name: f.properties.name });
          }
        }
      }}
    >
      <NavigationControl position="top-right" showCompass={false} />
      <Source id="hexes" type="geojson" data={hexGeoJSON}>
        <Layer
          id="hex-fill"
          type="fill"
          paint={{
            "fill-color": "#6b6f78",
            "fill-opacity": [
              "case",
              ["boolean", ["get", "is_unlocked"], false],
              0.0,
              0.72,
            ],
          }}
        />
        <Layer
          id="hex-outline"
          type="line"
          paint={{
            "line-color": "#3a3d45",
            "line-width": 0.6,
            "line-opacity": [
              "case",
              ["boolean", ["get", "is_unlocked"], false],
              0.0,
              0.5,
            ],
          }}
        />
      </Source>

      <Source id="partners" type="geojson" data={partnersGeoJSON}>
        <Layer
          id="partners-circle"
          type="circle"
          paint={{
            "circle-radius": 6,
            "circle-color": [
              "match",
              ["get", "category"],
              "restaurant", CATEGORY_COLORS.restaurant,
              "grocery", CATEGORY_COLORS.grocery,
              "fuel", CATEGORY_COLORS.fuel,
              "other", CATEGORY_COLORS.other,
              "#3D5A80",
            ],
            "circle-stroke-color": "#ffffff",
            "circle-stroke-width": 1.5,
          }}
        />
        <Layer
          id="partners-selected"
          type="circle"
          filter={["==", ["get", "partner_id"], selectedId ?? "__none__"]}
          paint={{
            "circle-radius": 12,
            "circle-color": "#FFD60A",
            "circle-opacity": 0,
            "circle-stroke-color": "#FFD60A",
            "circle-stroke-width": 3,
          }}
        />
      </Source>

      <Source id="pending" type="geojson" data={pendingGeoJSON}>
        <Layer
          id="pending-halo"
          type="circle"
          paint={{
            "circle-radius": pulse,
            "circle-color": "#FFD60A",
            "circle-opacity": 0.25,
            "circle-stroke-color": "#FFD60A",
            "circle-stroke-width": 2,
            "circle-stroke-opacity": 0.9,
          }}
        />
        <Layer
          id="pending-circle"
          type="circle"
          paint={{
            "circle-radius": 9,
            "circle-color": "#FFD60A",
            "circle-stroke-color": "#0d0d1a",
            "circle-stroke-width": 2,
          }}
        />
      </Source>

    </Map>
  );
}
