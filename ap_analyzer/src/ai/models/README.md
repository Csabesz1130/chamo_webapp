# AI Modellek

Ez a könyvtár a pre-trainelt AI modelleket tartalmazza a jelanalízishez.

## Modell struktúra

A modellek a következő formátumban kerülnek tárolásra:

```
models/
  ├── curve_type/
  │   ├── model.h5
  │   └── config.json
  └── parameter_optimization/
      ├── model.h5
      └── config.json
```

## Modell típusok

1. **Görbetípus előrejelzés**
   - Input: Idősor és jelértékek
   - Output: Görbe típusa (hiperpolarizáció, depolarizáció, stb.)

2. **Paraméteroptimalizálás**
   - Input: Idősor, jelértékek és görbetípus
   - Output: Optimalizált görbeparaméterek

## Modell betöltés

A modellek automatikusan betöltődnek az alkalmazás indításakor a `SignalAnalyzer` osztály által. 