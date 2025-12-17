# --------------------------------------------
# Course: CS 305 - Operating Systems
# Student: Melek Arslan
# Student ID: 220446018
# Assignment: Process Scheduling Simulator
# File: scheduler.py
# Date: 12-12-2025
# --------------------------------------------

import sys
from collections import deque

def parse_input_file(filename):
    """
    hocam burada input dosyasını okuyup satır satır ayırıyorum.
    formatımız: process_id, arrival_time, burst_time, priority
    """
    procs = []
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                # boş satırsa ya da '#' ile başlayan yorum satırıysa atlıyorum
                if not line or line.startswith('#'):
                    continue
                parts = [p.strip() for p in line.split(',')]
                # eğer satırda eksik bilgi varsa okumuyorum hata vermesin diye
                if len(parts) < 4:
                    continue  
                pid = parts[0]
                arrival = int(parts[1])
                burst = int(parts[2])
                priority = int(parts[3])
                procs.append((pid, arrival, burst, priority))
    except FileNotFoundError:
        print(f"hata: '{filename}' dosyayı bulamadım hocam.")
        sys.exit(1)
    except ValueError as e:
        print(f"dosya formatında sıkıntı var: {e}")
        sys.exit(1)
    return procs

def format_gantt(gantt):
    """
    gantt şemasını string olarak birleştiriyorum çıktı güzel görünsün diye.
    örnek: [0]--P1--[5]--P2--[10]
    """
    pieces = []
    for label, s, e in gantt:
        pieces.append(f"[{s}]--{label}--[{e}]")
    return ''.join(pieces)

def print_table(results, order):
    """
    hesapladığım metrikleri (finish, turnaround, waiting) tablo yapıp basıyorum.
    """
    print(" Process   | Finish Time | Turnaround Time | Waiting Time")
    print(" -----------------------------------------------------")
    for pid in order:
        r = results[pid]
        # sayıları ortaladım ki tablo kaymasın
        print(f" {pid:<10}| {r['finish']:^11} | {r['turnaround']:^15} | {r['waiting']:^12}")

def compute_averages(results):
    # ortalamaları burada alıyorum
    n = len(results)
    if n == 0: return 0.0, 0.0
    avg_tat = sum(results[p]['turnaround'] for p in results) / n
    avg_wt  = sum(results[p]['waiting'] for p in results) / n
    return avg_tat, avg_wt

# ---------------- algoritma kısımları -------------------

def simulate_fcfs(processes):
    """first-come, first-served (non-preemptive)"""
    
    # hocam fcfs olduğu için geliş zamanına (arrival) göre sıraladım
    procs_sorted = sorted(processes, key=lambda x: (x[1],))
    time = 0
    gantt = []
    idle = 0
    res = {}
    
    for pid, arr, burst, pri in procs_sorted:
        # eğer process gelmediyse cpu boş beklesin (idle)
        if time < arr:
            gantt.append(("idle", time, arr))
            idle += arr - time
            time = arr
        
        # işlemi çalıştırıyorum
        start = time
        end = time + burst
        gantt.append((pid, start, end))
        time += burst
        
        # değerleri hesaplayıp sözlüğe atıyorum
        res[pid] = {
            'finish': time, 
            'turnaround': time - arr, 
            'waiting': (time - arr) - burst
        }
        
    total_time = time
    # cpu kullanım yüzdesi hesabı
    cpu_util = (total_time - idle) / total_time * 100 if total_time > 0 else 0.0
    return res, gantt, cpu_util, total_time

def simulate_sjf(processes):
    """shortest job first (non-preemptive)"""
    
    # listeyi bozmamak için kopyasını aldım
    procs = [list(p) for p in processes]
    procs.sort(key=lambda x: x[1])
    
    n = len(procs)
    time = 0
    gantt = []
    idle = 0
    res = {}
    completed = 0
    
    # hepsi bitene kadar dönüyorum
    while completed < n:
        # şu ana kadar gelmiş ve bitmemiş olanları buluyorum
        candidates = [p for p in procs if p[1] <= time and ('done' not in p)]
        
        if not candidates:
            # kimse yoksa bir sonraki process gelene kadar zamanı ilerlettim
            next_arr = min(p[1] for p in procs if 'done' not in p)
            if time < next_arr:
                gantt.append(("idle", time, next_arr))
                idle += next_arr - time
                time = next_arr
            continue
            
        # hocam sjf mantığı: burst süresi en kısa olanı seçtim.
        # eğer süreler eşitse geliş zamanına baktım (fcfs gibi).
        candidates.sort(key=lambda x: (x[2], x[1]))
        p = candidates[0]
        
        pid, arr, burst, pri = p[0], p[1], p[2], p[3]
        
        # non-preemptive olduğu için bitene kadar çalışıyor
        gantt.append((pid, time, time + burst))
        time += burst
        
        res[pid] = {
            'finish': time, 
            'turnaround': time - arr, 
            'waiting': (time - arr) - burst
        }
        p.append('done') # bitti diye işaret koydum
        completed += 1
        
    total_time = time
    cpu_util = (total_time - idle) / total_time * 100 if total_time > 0 else 0.0
    return res, gantt, cpu_util, total_time

def simulate_rr(processes, tq):
    """round robin (preemptive) - tq parametresi önemli"""
    
    # her processin ne kadar süresi kaldı (rem) onu takip ediyorum
    procs_map = {p[0]: {'arr':p[1], 'rem':p[2], 'burst':p[2], 'pri':p[3]} for p in processes}
    
    time = 0
    gantt = []
    idle = 0
    ready = deque() # kuyruk yapısı için deque kullandım, daha pratik
    arrived = set() # kuyruğa girenleri not ediyorum
    n = len(processes)
    completed = 0

    # belli bir t anında gelenleri kuyruğa ekleyen fonksiyonum
    def add_arrivals_at(t):
        for p in processes:
            if p[1] == t and p[0] not in arrived:
                ready.append(p[0])
                arrived.add(p[0])

    # t=0 da gelen var mı diye baktım
    add_arrivals_at(0)
    
    # kimse yoksa ilk gelene kadar bekle
    if not ready:
        next_arr = min(p[1] for p in processes)
        gantt.append(("idle", time, next_arr))
        idle += next_arr - time
        time = next_arr
        add_arrivals_at(time)

    while completed < n:
        if not ready:
            # kuyruk boş ama bitmeyen işler varsa idle bekledim
            remaining_procs = [p for p in processes if p[0] not in arrived]
            if not remaining_procs: 
                break 
            
            next_arr = min(p[1] for p in remaining_procs)
            gantt.append(("idle", time, next_arr))
            idle += next_arr - time
            time = next_arr
            add_arrivals_at(time)
            continue
            
        pid = ready.popleft() # sıradakini aldım
        p = procs_map[pid]
        
        # tq kadar mı çalışacak yoksa daha az mı kaldı?
        run_time = min(tq, p['rem'])
        start = time
        end = time + run_time
        
        gantt.append((pid, start, end))
        
        # hocam burası kritik: işlem çalışırken (start -> end arası) yeni gelenleri kaçırmamak için
        # saniye saniye kontrol edip kuyruğa ekledim
        for t in range(start + 1, end + 1):
            add_arrivals_at(t)
            
        time = end
        p['rem'] -= run_time # çalışılan süreyi düştüm
        
        if p['rem'] == 0:
            completed += 1
            procs_map[pid]['finish'] = time
        else:
            # bitmediyse kuyruğun en arkasına geri gönderdim
            ready.append(pid)
            
    # sonuçları toparlıyorum
    res = {}
    for pid, vals in procs_map.items():
        res[pid] = {
            'finish': vals['finish'], 
            'turnaround': vals['finish'] - vals['arr'], 
            'waiting': (vals['finish'] - vals['arr']) - vals['burst']
        }
        
    total_time = time
    cpu_util = (total_time - idle) / total_time * 100 if total_time > 0 else 0.0
    return res, gantt, cpu_util, total_time

def simulate_priority(processes):
    """priority scheduling (non-preemptive) - düşük sayı yüksek öncelik demek"""
    procs = [list(p) for p in processes]
    procs.sort(key=lambda x: x[1])
    
    n = len(procs)
    time = 0
    gantt = []
    idle = 0
    res = {}
    completed = 0
    
    while completed < n:
        candidates = [p for p in procs if p[1] <= time and ('done' not in p)]
        
        if not candidates:
            next_arr = min(p[1] for p in procs if 'done' not in p)
            if time < next_arr:
                gantt.append(("idle", time, next_arr))
                idle += next_arr - time
                time = next_arr
            continue
            
        # önce prioritye göre (küçükten büyüğe), eşitse geliş sırasına göre sıraladım..
        candidates.sort(key=lambda x: (x[3], x[1]))
        p = candidates[0]
        
        pid, arr, burst, pri = p[0], p[1], p[2], p[3]
        
        gantt.append((pid, time, time + burst))
        time += burst
        
        res[pid] = {
            'finish': time, 
            'turnaround': time - arr, 
            'waiting': (time - arr) - burst
        }
        p.append('done')
        completed += 1
        
    total_time = time
    cpu_util = (total_time - idle) / total_time * 100 if total_time > 0 else 0.0
    return res, gantt, cpu_util, total_time

# ---------------- main / çalıştırma kısmı ----------------

def run_all(processes, rr_tq):
    # çıktı tablosunda karışıklık olmasın diye arrival time'a göre sıralı basıyorum.
    print_order = [p[0] for p in sorted(processes, key=lambda x: x[1])]
    
    algos = [
        ("FCFS", simulate_fcfs, None),
        ("SJF", simulate_sjf, None),
        (f"Round Robin (tq={rr_tq})", lambda p: simulate_rr(p, rr_tq), None),
        ("Priority", simulate_priority, None)
    ]
    
    for name, func, _ in algos:
        results, gantt, cpu_util, total_time = func(processes)
        print(f"\n--- scheduling algorithm: {name} ---")
        print("gantt chart:", format_gantt(gantt))
        print()
        print_table(results, print_order)
        
        avg_tat, avg_wt = compute_averages(results)
        print()
        print(f"average turnaround time: {avg_tat:.2f}")
        print(f"average waiting time: {avg_wt:.2f}")
        print(f"cpu utilization: {cpu_util:.1f}%")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("kullanım: python scheduler.py <girdi_dosyasi> [time_quantum]")
        sys.exit(1)
        
    input_file = sys.argv[1]
    
    # time quantum girilmezse varsayılan 3 olsun dedim ve rr_tq=3
    rr_tq = 3
    if len(sys.argv) >= 3:
        try:
            rr_tq = int(sys.argv[2])
        except ValueError:
            print("uyarı: time quantum hatalı, varsayılan (3) kullanıyorum.")

    procs = parse_input_file(input_file)
    run_all(procs, rr_tq)