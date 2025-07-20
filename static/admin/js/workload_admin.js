document.addEventListener('DOMContentLoaded', function() {
    // 工数フィールドの合計を計算する機能
    const dayFields = document.querySelectorAll('input[id*="day_"]');
    
    function calculateTotal() {
        let total = 0;
        dayFields.forEach(field => {
            const value = parseFloat(field.value) || 0;
            total += value;
        });
        
        // 合計表示エリアがあれば更新
        const totalDisplay = document.getElementById('total-hours-display');
        if (totalDisplay) {
            totalDisplay.innerHTML = `
                <strong>合計: ${total.toFixed(1)}時間 (${(total/8).toFixed(1)}人日)</strong>
                <br><small>※ 8時間 = 1人日で計算</small>
            `;
        }
    }
    
    // 各フィールドに変更イベントを追加
    dayFields.forEach(field => {
        field.addEventListener('change', calculateTotal);
        field.addEventListener('input', calculateTotal);
        
        // リアルタイム計算のためのキーアップイベントも追加
        field.addEventListener('keyup', calculateTotal);
    });
    
    // 初期計算
    setTimeout(calculateTotal, 100); // DOM完全読み込み後に実行
    
    // 合計表示エリアを追加
    const fieldsetWorkload = document.querySelector('fieldset.wide');
    if (fieldsetWorkload && !document.getElementById('total-hours-display')) {
        const totalDiv = document.createElement('div');
        totalDiv.className = 'workload-summary';
        totalDiv.innerHTML = `
            <h3>📊 工数合計</h3>
            <p id="total-hours-display">計算中...</p>
        `;
        totalDiv.style.cssText = `
            background: #f8f9fa;
            border: 2px solid #007bff;
            border-radius: 8px;
            padding: 15px;
            margin: 15px 0;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        `;
        fieldsetWorkload.parentNode.insertBefore(totalDiv, fieldsetWorkload.nextSibling);
    }
    
    // フィールドのスタイリング改善
    dayFields.forEach(field => {
        field.style.cssText = `
            width: 80px;
            text-align: center;
            padding: 5px;
            border: 2px solid #ddd;
            border-radius: 4px;
            font-weight: bold;
        `;
        
        // フォーカス時のスタイル
        field.addEventListener('focus', function() {
            this.style.borderColor = '#007bff';
            this.style.boxShadow = '0 0 5px rgba(0,123,255,0.3)';
        });
        
        field.addEventListener('blur', function() {
            this.style.borderColor = '#ddd';
            this.style.boxShadow = 'none';
            
            // 値がある場合の背景色
            if (parseFloat(this.value || 0) > 0) {
                this.style.backgroundColor = '#e3f2fd';
            } else {
                this.style.backgroundColor = '#fff';
            }
        });
    });
});