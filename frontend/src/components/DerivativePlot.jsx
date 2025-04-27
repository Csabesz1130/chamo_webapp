import React, { useEffect, useState } from 'react';
import { Line } from 'react-chartjs-2';
import {
    Chart as ChartJS,
    CategoryScale,
    LinearScale,
    PointElement,
    LineElement,
    Title,
    Tooltip,
    Legend
} from 'chart.js';

ChartJS.register(
    CategoryScale,
    LinearScale,
    PointElement,
    LineElement,
    Title,
    Tooltip,
    Legend
);

const DerivativePlot = () => {
    const [data, setData] = useState({
        labels: [],
        datasets: [{
            label: 'Derivált',
            data: [],
            borderColor: 'rgb(75, 192, 192)',
            tension: 0.1
        }]
    });

    useEffect(() => {
        const eventSource = new EventSource('http://localhost:8000/stream-derivative');

        eventSource.onmessage = (event) => {
            const newPoint = JSON.parse(event.data);

            setData(prevData => ({
                labels: [...prevData.labels, newPoint.x],
                datasets: [{
                    ...prevData.datasets[0],
                    data: [...prevData.datasets[0].data, newPoint.y]
                }]
            }));
        };

        return () => {
            eventSource.close();
        };
    }, []);

    const options = {
        responsive: true,
        animation: {
            duration: 0
        },
        scales: {
            x: {
                title: {
                    display: true,
                    text: 'Idő (ms)'
                }
            },
            y: {
                title: {
                    display: true,
                    text: 'Derivált (pA/ms)'
                }
            }
        }
    };

    return (
        <div style={{ width: '800px', height: '400px' }}>
            <Line data={data} options={options} />
        </div>
    );
};

export default DerivativePlot; 