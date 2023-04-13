

test-case-1
	throughput_udp_iperf_h1-h4.txt
		h1> iperf -c 10.0.5.2 -u -b 28M | tee measurements/test-case-1/t
		h4> iperf -s -u
	throughput_udp_iperf_h1-h9.txt
		h1> iperf -c 10.0.7.2 -u -b 20M | tee measurements/test-case-1/
		h9> iperf -s -u
	throughput_udp_iperf_h7-h9.txt
		h7> iperf -c 10.0.7.2 -u -b 20M | tee measurements/test-case-1/
		h9> iperf -s -u

test-case-2
	latency_L1.txt
		mininet> r1 ping r2 -c 25 | tee measurements/test-case-2/latency_L1.txt
	latency_L2.txt
		mininet> r2 ping r3 -c 25 | tee measurements/test-case-2/latency_L2.txt
	latency_L3.txt
		mininet> r3 ping r4 -c 25 | tee measurements/test-case-2/latency_L3.txt

