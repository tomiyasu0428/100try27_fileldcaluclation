// グローバル変数として定義
let map;

// indexページ用：登録済み農地のポリゴンを描画する関数
function initMap(fields) {
    try {
        map = new google.maps.Map(document.getElementById('map'), {
            center: { lat: 35.6895, lng: 139.6917 },
            zoom: 16
        });

        if (fields && fields.length > 0) {
            fields.forEach(function(field) {
                var polygon = new google.maps.Polygon({
                    paths: field.coordinates,
                    strokeColor: "#FF0000",
                    strokeOpacity: 0.8,
                    strokeWeight: 2,
                    fillColor: "#FF0000",
                    fillOpacity: 0.35,
                    map: map
                });
                var infoWindow = new google.maps.InfoWindow({
                    content: '<strong>' + field.name + '</strong><br>面積: ' + field.area + ' ha'
                });
                google.maps.event.addListener(polygon, 'click', function(event) {
                    infoWindow.setPosition(event.latLng);
                    infoWindow.open(map);
                });
            });
        }
        return map;
    } catch (error) {
        console.error('Map initialization error:', error);
        alert('マップの初期化中にエラーが発生しました。Google Maps APIキーが正しく設定されているか確認してください。');
    }
}

// ダッシュボード用：小さなマップに圃場を表示する関数
function initSmallMap(elementId, coordinates, fieldName) {
    try {
        var mapElement = document.getElementById(elementId);
        if (!mapElement) return;
        
        var smallMap = new google.maps.Map(mapElement, {
            disableDefaultUI: true,
            zoomControl: false,
            streetViewControl: false,
            mapTypeControl: false,
            fullscreenControl: false
        });
        
        var polygon = new google.maps.Polygon({
            paths: coordinates,
            strokeColor: "#FF0000",
            strokeOpacity: 0.8,
            strokeWeight: 2,
            fillColor: "#FF0000",
            fillOpacity: 0.35,
            map: smallMap
        });
        
        // ポリゴンの境界に合わせて表示範囲を調整
        var bounds = new google.maps.LatLngBounds();
        coordinates.forEach(function(coord) {
            bounds.extend(new google.maps.LatLng(coord.lat, coord.lng));
        });
        smallMap.fitBounds(bounds);
        
        return smallMap;
    } catch (error) {
        console.error('Small map initialization error:', error);
        // 小さなマップなのでエラーメッセージは非表示
    }
}

// 住所検索機能
function searchAddress() {
    try {
        const geocoder = new google.maps.Geocoder();
        const address = document.getElementById('address').value;

        geocoder.geocode({ address: address }, function(results, status) {
            if (status === 'OK') {
                const location = results[0].geometry.location;
                map.setCenter(location);
                map.setZoom(18); // より詳細な表示にズーム
            } else {
                alert('住所が見つかりませんでした: ' + status);
            }
        });
    } catch (error) {
        console.error('Geocoding error:', error);
        alert('住所検索中にエラーが発生しました。Google Maps APIキーが正しく設定されているか確認してください。');
    }
}

// 新規登録用：Drawing Library を用いてポリゴンを描画する関数
function initMapForDrawing(callback) {
    try {
        map = new google.maps.Map(document.getElementById('map'), {
            center: { lat: 35.6895, lng: 139.6917 },
            zoom: 16
        });

        var drawingManager = new google.maps.drawing.DrawingManager({
            drawingMode: google.maps.drawing.OverlayType.POLYGON,
            drawingControl: true,
            drawingControlOptions: {
                position: google.maps.ControlPosition.TOP_CENTER,
                drawingModes: [google.maps.drawing.OverlayType.POLYGON]
            },
            polygonOptions: {
                fillColor: '#FF0000',
                fillOpacity: 0.35,
                strokeWeight: 2,
                clickable: true,
                editable: true,
                zIndex: 1
            }
        });

        drawingManager.setMap(map);

        google.maps.event.addListener(drawingManager, 'polygoncomplete', function(polygon) {
            // ポリゴン描画完了時の処理
            updatePolygonData(polygon, callback);

            // ポリゴンの頂点が変更された時の処理
            google.maps.event.addListener(polygon.getPath(), 'set_at', function() {
                updatePolygonData(polygon, callback);
            });
            google.maps.event.addListener(polygon.getPath(), 'insert_at', function() {
                updatePolygonData(polygon, callback);
            });
            google.maps.event.addListener(polygon.getPath(), 'remove_at', function() {
                updatePolygonData(polygon, callback);
            });
        });

        return map;
    } catch (error) {
        console.error('Drawing map initialization error:', error);
        alert('マップの初期化中にエラーが発生しました。Google Maps APIキーが正しく設定されているか確認してください。');
    }
}

// 編集用：既存のポリゴン情報を編集するための初期化関数
function initMapForEditing(existingCoordinates, callback) {
    try {
        map = new google.maps.Map(document.getElementById('map'), {
            center: existingCoordinates[0],
            zoom: 16
        });

        var polygon = new google.maps.Polygon({
            paths: existingCoordinates,
            strokeColor: "#FF0000",
            strokeOpacity: 0.8,
            strokeWeight: 2,
            fillColor: "#FF0000",
            fillOpacity: 0.35,
            editable: true,
            map: map
        });

        google.maps.event.addListener(polygon.getPath(), 'set_at', function() {
            updatePolygonData(polygon, callback);
        });
        google.maps.event.addListener(polygon.getPath(), 'insert_at', function() {
            updatePolygonData(polygon, callback);
        });
        google.maps.event.addListener(polygon.getPath(), 'remove_at', function() {
            updatePolygonData(polygon, callback);
        });
        updatePolygonData(polygon, callback);
    } catch (error) {
        console.error('Editing map initialization error:', error);
        alert('マップの初期化中にエラーが発生しました。Google Maps APIキーが正しく設定されているか確認してください。');
    }
}

// 座標情報の更新と面積計算
function updatePolygonData(polygon, callback) {
    try {
        var coordinates = [];
        var path = polygon.getPath();
        path.forEach(function(coord) {
            coordinates.push({
                lat: coord.lat(),
                lng: coord.lng()
            });
        });

        // ヘクタール単位で面積を計算
        var area = google.maps.geometry.spherical.computeArea(path.getArray()) / 10000;
        area = Math.round(area * 100) / 100; // 小数点2桁に丸める

        if (callback) {
            callback(coordinates, area);
        }
    } catch (error) {
        console.error('Polygon data update error:', error);
        alert('ポリゴンデータの更新中にエラーが発生しました。');
    }
}
