#!/usr/bin/env node
/**
 * Palette validation script for colorblind safety, chroma floor, lightness, and contrast.
 * Validates categorical color pairs for academic figures and dashboards.
 */

function hexToRgb(hex) {
  hex = hex.replace(/^#/, '');
  if (hex.length === 3) {
    hex = hex.split('').map(c => c + c).join('');
  }
  const num = parseInt(hex, 16);
  return [num >> 16, (num >> 8) & 255, num & 255];
}

function srgbToLinear(c) {
  c = c / 255;
  return c <= 0.04045 ? c / 12.92 : Math.pow((c + 0.055) / 1.055, 2.4);
}

function linearToSrgb(c) {
  const clamped = Math.max(0, Math.min(1, c));
  return clamped <= 0.0031308
    ? clamped * 12.92 * 255
    : (1.055 * Math.pow(clamped, 1 / 2.4) - 0.055) * 255;
}

function rgbToXyz(rgb) {
  const r = srgbToLinear(rgb[0]);
  const g = srgbToLinear(rgb[1]);
  const b = srgbToLinear(rgb[2]);

  // sRGB D65 matrix
  const x = r * 0.4124564 + g * 0.3575761 + b * 0.1804375;
  const y = r * 0.2126729 + g * 0.7151522 + b * 0.0721750;
  const z = r * 0.0193339 + g * 0.1191920 + b * 0.9503041;
  return [x, y, z];
}

function xyzToLab(xyz) {
  // D65 reference white
  const xn = 0.95047;
  const yn = 1.00000;
  const zn = 1.08883;

  const f = t => t > 0.008856 ? Math.cbrt(t) : (7.787 * t) + (16 / 116);

  const fx = f(xyz[0] / xn);
  const fy = f(xyz[1] / yn);
  const fz = f(xyz[2] / zn);

  const L = Math.max(0, 116 * fy - 16);
  const a = 500 * (fx - fy);
  const b = 200 * (fy - fz);
  return [L, a, b];
}

function rgbToLab(rgb) {
  return xyzToLab(rgbToXyz(rgb));
}

function labChroma(lab) {
  return Math.sqrt(lab[1] * lab[1] + lab[2] * lab[2]);
}

function deltaE76(lab1, lab2) {
  const dL = lab1[0] - lab2[0];
  const da = lab1[1] - lab2[1];
  const db = lab1[2] - lab2[2];
  return Math.sqrt(dL * dL + da * da + db * db);
}

// Brettel / Vienot 1999 CVD simulation
function simulateCVD(rgb, type) {
  const r = srgbToLinear(rgb[0]);
  const g = srgbToLinear(rgb[1]);
  const b = srgbToLinear(rgb[2]);

  let simR = r, simG = g, simB = b;
  if (type === 'protanopia') {
    simR = 0.56667 * r + 0.43333 * g;
    simG = 0.55833 * r + 0.44167 * g;
    simB = 0.24167 * g + 0.75833 * b;
  } else if (type === 'deuteranopia') {
    simR = 0.625 * r + 0.375 * g;
    simG = 0.70 * r + 0.30 * g;
    simB = 0.30 * g + 0.70 * b;
  } else if (type === 'tritanopia') {
    simR = 0.95 * r + 0.05 * g;
    simG = 0.43333 * g + 0.56667 * b;
    simB = 0.475 * g + 0.525 * b;
  }

  return [
    Math.round(linearToSrgb(simR)),
    Math.round(linearToSrgb(simG)),
    Math.round(linearToSrgb(simB))
  ];
}

function relativeLuminance(rgb) {
  const r = srgbToLinear(rgb[0]);
  const g = srgbToLinear(rgb[1]);
  const b = srgbToLinear(rgb[2]);
  return 0.2126 * r + 0.7152 * g + 0.0722 * b;
}

function contrastRatio(rgb1, rgb2) {
  const l1 = relativeLuminance(rgb1);
  const l2 = relativeLuminance(rgb2);
  const lighter = Math.max(l1, l2);
  const darker = Math.min(l1, l2);
  return (lighter + 0.05) / (darker + 0.05);
}

function validate(hexStr, options = {}) {
  const mode = options.mode || 'light';
  const surfaceHex = options.surface || (mode === 'dark' ? '#0e1117' : '#ffffff');
  const surfaceRgb = hexToRgb(surfaceHex);

  const colors = hexStr.split(',').map(s => s.trim());
  let allPass = true;
  const results = [];

  console.log(`\n=======================================================`);
  console.log(`PALETTE VALIDATION REPORT`);
  console.log(`Mode: ${mode.toUpperCase()} | Surface: ${surfaceHex}`);
  console.log(`Palette: ${colors.join(', ')}`);
  console.log(`=======================================================\n`);

  // 1. Per-color checks: Lightness, Chroma, Contrast
  console.log(`--- [1] Per-Color Metrics & Checks ---`);
  const CHROMA_FLOOR = 38.0; // Chroma floor for vibrant, non-grayed categorical blue/orange
  const MIN_CONTRAST = mode === 'dark' ? 3.0 : 3.0; // Graphical objects WCAG AA standard

  const labs = [];
  colors.forEach(hex => {
    const rgb = hexToRgb(hex);
    const lab = rgbToLab(rgb);
    labs.push(lab);
    const chroma = labChroma(lab);
    const contrast = contrastRatio(rgb, surfaceRgb);

    let chromaPass = chroma >= CHROMA_FLOOR;
    let lightnessPass = true;
    if (mode === 'dark') {
      lightnessPass = lab[0] >= 45.0; // Needs sufficient lightness on dark surface
    } else {
      lightnessPass = lab[0] <= 85.0 && lab[0] >= 20.0;
    }
    let contrastPass = contrast >= MIN_CONTRAST;

    const pass = chromaPass && lightnessPass && contrastPass;
    if (!pass) allPass = false;

    console.log(`Color ${hex}:`);
    console.log(`  - Lightness (L*): ${lab[0].toFixed(1)} [${lightnessPass ? 'PASS' : 'FAIL'}]`);
    console.log(`  - Chroma (C*):    ${chroma.toFixed(1)} (floor: ${CHROMA_FLOOR}) [${chromaPass ? 'PASS' : 'FAIL'}]`);
    console.log(`  - Contrast vs BG: ${contrast.toFixed(2)}:1 (min: ${MIN_CONTRAST}:1) [${contrastPass ? 'PASS' : 'FAIL'}]`);
    console.log(`  -> Status: ${pass ? 'PASS' : 'FAIL'}`);
  });

  // 2. CVD Separation Check
  console.log(`\n--- [2] Pairwise CVD Separation Checks (min ΔE >= 15.0) ---`);
  for (let i = 0; i < colors.length; i++) {
    for (let j = i + 1; j < colors.length; j++) {
      const c1 = colors[i];
      const c2 = colors[j];
      const rgb1 = hexToRgb(c1);
      const rgb2 = hexToRgb(c2);

      const deNormal = deltaE76(rgbToLab(rgb1), rgbToLab(rgb2));
      const deProtan = deltaE76(rgbToLab(simulateCVD(rgb1, 'protanopia')), rgbToLab(simulateCVD(rgb2, 'protanopia')));
      const deDeuter = deltaE76(rgbToLab(simulateCVD(rgb1, 'deuteranopia')), rgbToLab(simulateCVD(rgb2, 'deuteranopia')));
      const deTritan = deltaE76(rgbToLab(simulateCVD(rgb1, 'tritanopia')), rgbToLab(simulateCVD(rgb2, 'tritanopia')));

      const cvdMin = Math.min(deNormal, deProtan, deDeuter, deTritan);
      const cvdPass = cvdMin >= 15.0;
      if (!cvdPass) allPass = false;

      console.log(`Pair (${c1}, ${c2}):`);
      console.log(`  - Normal ΔE:       ${deNormal.toFixed(1)}`);
      console.log(`  - Protanopia ΔE:   ${deProtan.toFixed(1)}`);
      console.log(`  - Deuteranopia ΔE: ${deDeuter.toFixed(1)}`);
      console.log(`  - Tritanopia ΔE:   ${deTritan.toFixed(1)}`);
      console.log(`  - CVD ΔE Range:    ${cvdMin.toFixed(1)} - ${Math.max(deNormal, deProtan, deDeuter, deTritan).toFixed(1)}`);
      console.log(`  -> CVD Separation Status: ${cvdPass ? 'PASS' : 'FAIL'}`);
    }
  }

  console.log(`\n=======================================================`);
  if (allPass) {
    console.log(`RESULT: ALL CHECKS PASS`);
  } else {
    console.log(`RESULT: CHECKS FAILED`);
  }
  console.log(`=======================================================\n`);
  return allPass;
}

// CLI argument parsing
const args = process.argv.slice(2);
let paletteArg = null;
let mode = 'light';
let surface = null;

for (let i = 0; i < args.length; i++) {
  if (args[i] === '--mode') {
    mode = args[++i];
  } else if (args[i] === '--surface') {
    surface = args[++i];
  } else if (!args[i].startsWith('--')) {
    paletteArg = args[i];
  }
}

if (!paletteArg) {
  console.error('Usage: node validate_palette.js "<hex,hex>" [--mode light|dark] [--surface "<hex>"]');
  process.exit(1);
}

const passed = validate(paletteArg, { mode, surface });
process.exit(passed ? 0 : 1);
