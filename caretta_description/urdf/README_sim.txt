FS-1 Caretta Rev G - Gazebo / URDF paketi
- meshes/*.stl: metre biriminde, her biri kendi link cercevesinde (visual origin = 0).
- base_link: donme merkezi = teker ekseni orta noktasi, zeminde (x ileri, y sol, z yukari).
  Plaka koordinati -> URDF: x_urdf = (x_plaka - 45 mm).
- Rev G: aks plaka merkezinin 45 mm onunde, motorlar 180 derece cevrildi (govde arkaya),
  tek arka sarhos teker -> 3 temas noktasi (2 teker + caster).

Diff drive degerleri:
  wheel_separation 0.2092 m, wheel_radius 0.0345 m
  joint'ler: caretta_left_wheel, caretta_right_wheel (eksen 0 1 0, ikisi de + = ileri)
Cerceveler:
  root caretta_base_footprint -> caretta_base_link
  LiDAR link caretta_lidar (0, 0, 0.1172) = aksin ustu, tarama cercevesi caretta_laser (+0.029, optik basligin ortasi)
  kamera link caretta_camera (0.059, 0, 0.0982), goruntu cercevesi caretta_camera_optical
  caster caretta_ball_caster, bilye merkezi (-0.127, 0, 0.006)
Carpisma: govde = kutu, teker = silindir, caster = kure (mu=0), teker mu=1. Kutleler tahmini.

Not: base_link.stl ve caretta_motor.stl, Rev G zip'i olmadigi icin Rev E7 mesh'lerinden
turetildi (govde x -45 mm kaydirildi, motor z etrafinda 180 derece cevrildi). Sinirlar
Rev G README ile ayni; plaka delik detaylari E7'den. Rev G zip gelince degistirin.
