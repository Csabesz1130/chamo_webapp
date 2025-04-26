def calculate_range_integral_with_custom_start(self, custom_start_points=None):
    """
    Kiszámítja az integrálokat egyéni kezdőpontokkal.
    
    Args:
        custom_start_points: Egyéni kezdőpontok a hiperpol és depol görbékhez
    """
    if self.filtered_data is None:
        return
            
    try:
        # Akciós potenciál processzor lekérése a szülő alkalmazásból
        app = self.parent.parent.master
        if not hasattr(app, 'action_potential_processor') or app.action_potential_processor is None:
            self.integral_display.config(text="Futtasson analízist az integrálok megtekintéséhez")
            return
        
        processor = app.action_potential_processor
        
        # Ellenőrizzük, hogy van-e egyéni kezdőpont
        using_custom_points = False
        if custom_start_points and custom_start_points.get('enabled', False):
            points = custom_start_points.get('points', {})
            if 'hyperpol' in points and 'depol' in points:
                using_custom_points = True
        
        # Aktuális tartományok lekérése
        ranges = self.get_integration_ranges()
        
        try:
            # Hiperpolarizációs integrál számítása
            hyperpol_range = ranges['hyperpol']
            hyperpol_start = hyperpol_range['start']
            hyperpol_end = hyperpol_range['end']
            
            # Egyéni kezdőpont alkalmazása ha elérhető
            if using_custom_points:
                custom_hyperpol_start = points['hyperpol']
                if custom_hyperpol_start > hyperpol_start and custom_hyperpol_start < hyperpol_end:
                    hyperpol_start = custom_hyperpol_start
            
            # Ellenőrizzük, hogy az indexek érvényesek-e
            if (hasattr(processor, 'modified_hyperpol') and
                hyperpol_start < len(processor.modified_hyperpol) and 
                hyperpol_end <= len(processor.modified_hyperpol)):
                
                hyperpol_data = processor.modified_hyperpol[hyperpol_start:hyperpol_end]
                hyperpol_times = processor.modified_hyperpol_times[hyperpol_start:hyperpol_end]
                if len(hyperpol_data) > 1:
                    hyperpol_integral = np.trapz(hyperpol_data, x=hyperpol_times * 1000)
                else:
                    hyperpol_integral = 0
            else:
                hyperpol_integral = 0
            
            # Depolarizációs integrál számítása
            depol_range = ranges['depol']
            depol_start = depol_range['start']
            depol_end = depol_range['end']
            
            # Egyéni kezdőpont alkalmazása ha elérhető
            if using_custom_points:
                custom_depol_start = points['depol']
                if custom_depol_start > depol_start and custom_depol_start < depol_end:
                    depol_start = custom_depol_start
            
            # Ellenőrizzük, hogy az indexek érvényesek-e
            if (hasattr(processor, 'modified_depol') and
                depol_start < len(processor.modified_depol) and 
                depol_end <= len(processor.modified_depol)):
                
                depol_data = processor.modified_depol[depol_start:depol_end]
                depol_times = processor.modified_depol_times[depol_start:depol_end]
                if len(depol_data) > 1:
                    depol_integral = np.trapz(depol_data, x=depol_times * 1000)
                else:
                    depol_integral = 0
            else:
                depol_integral = 0
            
            # Megjelenítés frissítése egyéni kezdőpontok jelzésével
            if using_custom_points:
                self.integral_display.config(
                    text=f"Hiperpol integrál [EK]: {hyperpol_integral:.3f} pC\n"
                        f"Depol integrál [EK]: {depol_integral:.3f} pC"
                )
            else:
                self.integral_display.config(
                    text=f"Hiperpol integrál: {hyperpol_integral:.3f} pC\n"
                        f"Depol integrál: {depol_integral:.3f} pC"
                )
            
            # Eredmények tárolása későbbi hozzáféréshez
            self.current_integrals = {
                'hyperpol_integral': hyperpol_integral,
                'depol_integral': depol_integral,
                'custom_start_points': using_custom_points
            }
            
        except Exception as e:
            app_logger.error(f"Hiba az integrálok számításakor: {str(e)}")
            
    except Exception as e:
        app_logger.error(f"Hiba az integrálok frissítésekor egyéni kezdőpontokkal: {str(e)}") 