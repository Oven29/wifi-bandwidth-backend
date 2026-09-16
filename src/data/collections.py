
network_activity_profiles_db = [
    {
        "profile_id": 1,
        "profile_title": "4K Стриминг",
        "required_bandwidth_mbps": 100,
        "recommended_wifi_standard": "Wi-Fi 6 (802.11ax)",
        "min_device_ram_mb": 512,
        "traffic_priority_level": "High",
        "profile_status": "published",
        "preview_image_url": "http://localhost:9000/media/telek.png",
        "preview_video_url": "http://localhost:9000/media/telek.mp4",
        "liked_user_ids": [101, 102, 105]
    },
    {
        "profile_id": 2,
        "profile_title": "Онлайн Игры",
        "required_bandwidth_mbps": 50,
        "recommended_wifi_standard": "Wi-Fi 6 (802.11ax)",
        "min_device_ram_mb": 256,
        "traffic_priority_level": "Critical",
        "profile_status": "published",
        "preview_image_url": "http://localhost:9000/media/games.png",
        "preview_video_url": "http://localhost:9000/media/games.mp4",
        "liked_user_ids": [104, 105, 106, 107]
    },
    {
        "profile_id": 3,
        "profile_title": "Умные IoT Девайсы",
        "required_bandwidth_mbps": 25,
        "recommended_wifi_standard": "Wi-Fi 4 (802.11n)",
        "min_device_ram_mb": 128,
        "traffic_priority_level": "Standard",
        "profile_status": "published",
        "preview_image_url": "http://localhost:9000/media/iot.png",
        "preview_video_url": "http://localhost:9000/media/iot.mp4",
        "liked_user_ids": [108]
    },
    {
        "profile_id": 4,
        "profile_title": "Торрент & Облачный бэкап",
        "required_bandwidth_mbps": 300,
        "recommended_wifi_standard": "Wi-Fi 6 (802.11ax)",
        "min_device_ram_mb": 1024,
        "traffic_priority_level": "Background",
        "profile_status": "deleted",
        "preview_image_url": "http://localhost:9000/media/torrent.png",
        "preview_video_url": "http://localhost:9000/media/torrent.mp4",
        "liked_user_ids": []
    }
]
