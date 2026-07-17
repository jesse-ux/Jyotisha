use serde::Deserialize;
use serde_json::{json, Map, Value};
use std::io::{self, Read};
use xalen_vedic::ashtakavarga::{prashtarashtakavarga, sarvashtakavarga};
use xalen_vedic::divisional::{compute_varga_sign, VargaChart};
use xalen_vedic::nakshatra::DashaLord;
use xalen_vedic::shadbala::{PlanetPosition, ShadBalaInput, Shadbala};
use xalen_ayanamsa::Ayanamsa;
use xalen_coords::RAD_TO_DEG;
use xalen_ephem::{Almanac, Body as EphemBody};
use xalen_time::JdUT1;

const NAMES: [&str; 7] = ["Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn"];
const LORDS: [DashaLord; 7] = [DashaLord::Sun, DashaLord::Moon, DashaLord::Mars, DashaLord::Mercury, DashaLord::Jupiter, DashaLord::Venus, DashaLord::Saturn];

#[derive(Clone, Deserialize)]
struct Body { name: String, longitude: f64, speed: f64, house: usize }

#[derive(Deserialize)]
struct Input { jd: f64, day_fraction: f64, asc_sign_idx: usize, planets: Vec<Body>, mode: Option<String> }

fn varga(name: &str) -> VargaChart {
    match name { "D1" => VargaChart::D1, "D2" => VargaChart::D2, "D4" => VargaChart::D4, "D9" => VargaChart::D9, _ => VargaChart::D10 }
}

fn main() {
    let mut raw = String::new();
    io::stdin().read_to_string(&mut raw).unwrap();
    let input: Input = serde_json::from_str(&raw).unwrap();
    let mode = input.mode.as_deref().unwrap_or("shared_input");
    let effective = if mode == "independent_ephemeris" {
        let almanac = Almanac::default_vedic();
        let jd = JdUT1(input.jd);
        let aya = Ayanamsa::Lahiri.compute_deg(input.jd);
        let ephem = [EphemBody::Sun, EphemBody::Moon, EphemBody::Mars, EphemBody::Mercury, EphemBody::Jupiter, EphemBody::Venus, EphemBody::Saturn];
        NAMES.iter().enumerate().map(|(i, name)| {
            let original = input.planets.iter().find(|p| p.name == *name).unwrap();
            let pos = almanac.geocentric_ecliptic(ephem[i], jd).unwrap();
            let speed = almanac.geocentric_speed(ephem[i], jd).unwrap();
            Body { name: name.to_string(), longitude: (pos.longitude * RAD_TO_DEG - aya).rem_euclid(360.0), speed: speed.longitude * RAD_TO_DEG, house: original.house }
        }).collect()
    } else { input.planets.clone() };
    let bodies: Vec<&Body> = NAMES.iter().map(|name| effective.iter().find(|p| p.name == *name).unwrap()).collect();
    let positions: Vec<PlanetPosition> = bodies.iter().enumerate().map(|(i, p)| PlanetPosition { name: NAMES[i], longitude: p.longitude, speed: p.speed }).collect();
    let shad_input = ShadBalaInput { jd: input.jd, sun_lon: bodies[0].longitude, moon_lon: bodies[1].longitude, day_fraction: input.day_fraction, all_planets: positions };
    let sign_positions: Vec<(DashaLord, usize)> = bodies.iter().enumerate().map(|(i, p)| (LORDS[i], (p.longitude / 30.0) as usize % 12)).collect();

    let mut vargas = Map::new();
    for chart in ["D1", "D2", "D4", "D9", "D10"] {
        let values: Map<String, Value> = bodies.iter().enumerate().map(|(i, p)| (NAMES[i].to_string(), json!(format!("{:?}", compute_varga_sign(p.longitude, varga(chart)))))).collect();
        vargas.insert(chart.to_string(), Value::Object(values));
    }
    let mut shadbala = Map::new();
    for (i, p) in bodies.iter().enumerate() {
        let sb = Shadbala::compute_full(NAMES[i], p.longitude, p.house, p.speed, &shad_input);
        shadbala.insert(NAMES[i].to_string(), json!({"sthana": sb.sthana_bala.total, "dig": sb.dig_bala, "kala": sb.kala_bala.total, "chesta": sb.cheshta_bala, "naisargika": sb.naisargika_bala, "drik": sb.drik_bala, "total": sb.total, "rupas": sb.total / 60.0}));
    }
    let bav: Map<String, Value> = LORDS.iter().enumerate().map(|(i, lord)| (NAMES[i].to_string(), json!(prashtarashtakavarga(*lord, &sign_positions, input.asc_sign_idx)))).collect();
    let sav_rows = sarvashtakavarga(&sign_positions, input.asc_sign_idx);
    let sav: Vec<u16> = (0..12).map(|sign| sav_rows.iter().map(|row| row[sign] as u16).sum()).collect();
    let effective_positions: Map<String, Value> = bodies.iter().map(|p| (p.name.clone(), json!({"longitude":p.longitude,"speed":p.speed,"house":p.house}))).collect();
    println!("{}", json!({"engine":"xalen-ephemeris","commit":"cc6edbec1f748ebdc4950ae6198f575c5ada73fa","license":"Apache-2.0","ephemeris_mode":mode,"effective_positions":effective_positions,"varga":vargas,"ashtakavarga":{"bav":bav,"sav":sav},"shadbala":shadbala}));
}
