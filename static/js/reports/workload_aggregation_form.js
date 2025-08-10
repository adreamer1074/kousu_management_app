document.addEventListener('DOMContentLoaded', function() {
    const config = window.formConfig;
    if (!config) {
        console.error('formConfig が見つかりません');
        return;
    }

    console.log('=== 統合フォームJavaScript開始 ===');
    console.log('編集モード:', config.isEditMode);

    // === DOM要素の取得（workload_aggregation_form.js から） ===
    const projectSelect = document.getElementById(config.projectSelectId);
    const caseNameSelect = document.getElementById(config.caseNameSelectId);
    const classificationSelect = document.getElementById(config.classificationSelectId);
    const autoCalculateCheckbox = document.getElementById(config.autoCalculateCheckboxId);
    const usedWorkdaysField = document.getElementById(config.usedWorkdaysFieldId);
    const newbieWorkdaysField = document.getElementById(config.newbieWorkdaysFieldId);
    const orderDateInput = document.getElementById(config.orderDateInputId);
    const actualEndDateInput = document.getElementById(config.actualEndDateInputId);
    const calculateButton = document.getElementById('calculateWorkdays');
    const form = document.getElementById('workloadForm');
    
    // 計算対象フィールド
    const billingAmountField = document.getElementById(config.billingAmountFieldId);
    const outsourcingCostField = document.getElementById(config.outsourcingCostFieldId);
    const estimatedWorkdaysField = document.getElementById(config.estimatedWorkdaysFieldId);
    const availableAmountField = document.getElementById(config.availableAmountFieldId);
    const billingUnitCostField = document.getElementById(config.billingUnitCostFieldId);
    const unitCostField = document.getElementById(config.unitCostFieldId);
    const yearMonthField = config.yearMonthFieldId ? document.getElementById(config.yearMonthFieldId) : null;

    // 計算処理中フラグ（無限ループ防止）
    let isCalculating = false;

    // === 初期化処理 ===
    function initializeUnifiedForm() {
        console.log('=== 統合フォーム初期化 ===');
        
        // プロジェクト選択時の処理
        if (projectSelect) {
            projectSelect.addEventListener('change', function() {
                const projectId = this.value;
                console.log('プロジェクト変更:', projectId);
                
                // === 【編集時】同じプロジェクトの場合はスキップ ===
                if (config.isEditMode && config.currentProjectId == projectId) {
                    console.log('編集モード：同じプロジェクト選択、処理スキップ');
                    return;
                }
                
                // チケット選択をクリア
                if (caseNameSelect) {
                    caseNameSelect.innerHTML = '<option value="">チケット（案件）を選択してください</option>';
                }
                
                if (projectId) {
                    loadTicketsForProject(projectId);
                }
            });
            
            // === 【新規作成】初期状態でプロジェクトが選択されている場合 ===
            if (!config.isEditMode && projectSelect.value) {
                projectSelect.dispatchEvent(new Event('change'));
            }
        }

        // === 【編集時】初期外注費取得 ===
        if (config.isEditMode && config.currentTicketId) {
            console.log('編集モード：初期チケットで外注費取得:', config.currentTicketId);
            setTimeout(() => {
                fetchOutsourcingCost(config.currentTicketId);
            }, 500);
        }

        // チケット選択時の処理
        if (caseNameSelect) {
            caseNameSelect.addEventListener('change', function() {
                const ticketId = this.value;
                const selectedOption = this.options[this.selectedIndex];
                
                if (ticketId) {
                    console.log('チケット選択変更:', ticketId);
                    
                    // 外注費を取得
                    fetchOutsourcingCost(ticketId);
                    
                    if (autoCalculateCheckbox && autoCalculateCheckbox.checked) {
                        // チケット分類を自動設定
                        const classification = selectedOption.getAttribute('data-classification');
                        if (classification && classificationSelect) {
                            classificationSelect.value = classification;
                        }
                        
                        // 工数をリアルタイム計算
                        calculateWorkdays(ticketId, classification);
                    } else if (ticketId) {
                        // 工数を取得
                        fetchWorkHours(ticketId);
                    }
                } else {
                    // チケット未選択時は外注費をリセット
                    if (outsourcingCostField) {
                        outsourcingCostField.value = '0';
                        calculateValues();
                    }
                }
            });
        }

        // 自動計算機能の初期化
        setupUserModificationTracking();
        setupCalculationTriggers();
    }

    // === チケット読み込み ===
    function loadTicketsForProject(projectId) {
        const apiUrl = `${config.ticketsApiUrl}?project_id=${projectId}`;
        console.log('チケット読み込み:', apiUrl);
        
        if (!caseNameSelect) {
            console.error('チケット選択要素が見つかりません');
            return;
        }
        
        caseNameSelect.innerHTML = '<option value="">読み込み中...</option>';
        
        fetch(apiUrl)
            .then(response => {
                if (!response.ok) {
                    throw new Error(`HTTP error! status: ${response.status}`);
                }
                return response.json();
            })
            .then(data => {
                if (data.success) {
                    if (data.tickets && data.tickets.length > 0) {
                        caseNameSelect.innerHTML = '<option value="">チケット（案件）を選択してください</option>';
                        
                        data.tickets.forEach(ticket => {
                            const option = document.createElement('option');
                            option.value = ticket.id;
                            option.textContent = ticket.title;
                            option.setAttribute('data-classification', ticket.case_classification || '');
                            caseNameSelect.appendChild(option);
                        });
                        
                        console.log('チケット読み込み完了:', data.tickets.length, '件');
                    } else {
                        caseNameSelect.innerHTML = '<option value="">このプロジェクトにはチケットがありません</option>';
                    }
                } else {
                    console.error('チケット取得失敗:', data.error || '不明なエラー');
                    caseNameSelect.innerHTML = '<option value="">チケット取得に失敗しました</option>';
                }
            })
            .catch(error => {
                console.error('チケット取得エラー:', error);
                caseNameSelect.innerHTML = '<option value="">チケット取得中にエラーが発生しました</option>';
            });
    }

    // === 外注費取得関数 ===
    function fetchOutsourcingCost(ticketId) {
        if (!ticketId || !outsourcingCostField) return;
        
        console.log('外注費取得開始:', ticketId);
        
        // 現在の年月を取得（必要に応じて変更可能）
        const currentDate = new Date();
        const yearMonth = `${currentDate.getFullYear()}-${String(currentDate.getMonth() + 1).padStart(2, '0')}`;
        
        // ローディング表示
        outsourcingCostField.style.backgroundColor = '#fff3cd';
        outsourcingCostField.value = '取得中...';
        
        // 外注費取得API呼び出し
        fetch(`${config.outsourcingCostApiUrl}?ticket_id=${ticketId}&year_month=${yearMonth}`)
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    // 外注費フィールドに値を設定
                    setFieldValue(outsourcingCostField, Math.round(data.total_cost));
                    setAutoCalculatedStyle(outsourcingCostField);
                    
                    console.log('外注費取得成功:', data.total_cost);
                    
                    // 他の計算をトリガー
                    setTimeout(() => {
                        if (!isCalculating) calculateValues();
                    }, 100);
                    
                } else {
                    console.warn('外注費取得失敗:', data.error || '不明なエラー');
                    setFieldValue(outsourcingCostField, '0');
                    setManualEditStyle(outsourcingCostField);
                }
            })
            .catch(error => {
                console.error('外注費取得エラー:', error);
                setFieldValue(outsourcingCostField, '0');
                setManualEditStyle(outsourcingCostField);
            })
            .finally(() => {
                // ローディング解除
                outsourcingCostField.style.backgroundColor = '';
            });
    }

    // === 工数計算関数 ===
    function calculateWorkdays(ticketId, classification) {
        if (!ticketId) return;
        
        console.log('工数計算開始:', ticketId, classification);
        
        // ローディング表示
        if (usedWorkdaysField) {
            usedWorkdaysField.value = '計算中...';
            usedWorkdaysField.style.backgroundColor = '#fff3cd';
        }
        if (newbieWorkdaysField) {
            newbieWorkdaysField.value = '計算中...';
            newbieWorkdaysField.style.backgroundColor = '#fff3cd';
        }
        
        // AJAX で工数計算
        const formData = new FormData();
        formData.append('ticket_id', ticketId);
        formData.append('classification', classification || 'development');
        formData.append('csrfmiddlewaretoken', config.csrfToken);
        
        fetch(config.calculateWorkdaysUrl, {
            method: 'POST',
            body: formData
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                if (usedWorkdaysField) {
                    usedWorkdaysField.value = parseFloat(data.used_workdays).toFixed(1);
                    usedWorkdaysField.style.backgroundColor = '#d1edff';
                }
                if (newbieWorkdaysField) {
                    newbieWorkdaysField.value = parseFloat(data.newbie_workdays).toFixed(1);
                    newbieWorkdaysField.style.backgroundColor = '#d1edff';
                }
                
                console.log('工数計算成功:', data);
                
                // 自動計算を実行
                setTimeout(() => {
                    if (!isCalculating) calculateValues();
                }, 200);
            } else {
                console.error('工数計算エラー:', data.error);
                if (usedWorkdaysField) {
                    usedWorkdaysField.value = '0.0';
                    usedWorkdaysField.style.backgroundColor = '#f8d7da';
                }
                if (newbieWorkdaysField) {
                    newbieWorkdaysField.value = '0.0';
                    newbieWorkdaysField.style.backgroundColor = '#f8d7da';
                }
            }
        })
        .catch(error => {
            console.error('AJAX エラー:', error);
        });
    }

    // === 工数自動取得機能 ===
    async function fetchWorkHours(caseId) {
        if (!caseId) {
            if (usedWorkdaysField) usedWorkdaysField.value = '0.0';
            if (newbieWorkdaysField) newbieWorkdaysField.value = '0.0';
            setTimeout(() => {
                if (!isCalculating) calculateValues();
            }, 100);
            return;
        }
        
        try {
            const response = await fetch('/reports/api/calculate-workdays/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value
                },
                body: JSON.stringify({
                    case_id: caseId,
                    order_date: orderDateInput ? orderDateInput.value : null,
                    actual_end_date: actualEndDateInput ? actualEndDateInput.value : null
                })
            });
            
            if (response.ok) {
                const data = await response.json();
                
                if (data.success) {
                    if (usedWorkdaysField) usedWorkdaysField.value = data.used_workdays.toFixed(1);
                    if (newbieWorkdaysField) newbieWorkdaysField.value = data.newbie_workdays.toFixed(1);
                    
                    // 工数取得後に自動計算を実行
                    setTimeout(() => {
                        if (!isCalculating) calculateValues();
                    }, 100);
                } else {
                    console.error('工数取得エラー:', data.error);
                }
            }
        } catch (error) {
            console.error('工数取得エラー:', error);
        }
    }

    // === 自動計算機能 ===
    function calculateValues() {
        if (isCalculating) {
            console.log('計算処理中のため、スキップします');
            return;
        }
        
        isCalculating = true;
        console.log('=== 自動計算開始 ===');
        
        try {
            // 値の取得
            const billingAmount = parseFloat(billingAmountField?.value) || 0;
            const outsourcingCost = parseFloat(outsourcingCostField?.value) || 0;
            const estimatedWorkdays = parseFloat(estimatedWorkdaysField?.value) || 0;
            const usedWorkdays = parseFloat(usedWorkdaysField?.value) || 0;
            const newbieWorkdays = parseFloat(newbieWorkdaysField?.value) || 0;
            const unitCost = parseFloat(unitCostField?.value) || 0;
            const billingUnitCost = parseFloat(billingUnitCostField?.value) || 0;
            
            // 1. 使用可能金額(税別) = 請求金額(税別) - 外注費（税別）
            const actualAvailableAmount = Math.max(billingAmount - outsourcingCost, 0);
            
            // 使用可能金額の自動設定
            if (availableAmountField && availableAmountField.dataset.userModified !== 'true') {
                if (billingAmount > 0 || outsourcingCost > 0) {
                    setFieldValue(availableAmountField, Math.round(actualAvailableAmount));
                    setAutoCalculatedStyle(availableAmountField);
                }
            }
            
            // 2. 見積工数（人日）のデフォルト = 使用可能金額(税別) / (請求単価/20*10000)
            if (estimatedWorkdaysField && estimatedWorkdaysField.dataset.userModified !== 'true') {
                if (billingUnitCost > 0 && actualAvailableAmount > 0) {
                    const dailyRate = (billingUnitCost / 20) * 10000; // 万円→円変換
                    const defaultEstimatedWorkdays = actualAvailableAmount / dailyRate;
                    
                    if (defaultEstimatedWorkdays > 0 && isFinite(defaultEstimatedWorkdays)) {
                        setFieldValue(estimatedWorkdaysField, defaultEstimatedWorkdays.toFixed(1));
                        setAutoCalculatedStyle(estimatedWorkdaysField);
                    }
                }
            }
            
            // 3. 使用工数合計計算
            const totalUsedWorkdays = usedWorkdays + newbieWorkdays;
            const totalUsedWorkdaysElement = document.getElementById('totalUsedWorkdays');
            if (totalUsedWorkdaysElement) {
                totalUsedWorkdaysElement.textContent = `${totalUsedWorkdays.toFixed(1)}人日`;
            }
            
            // 4. 残工数計算
            const currentEstimatedWorkdays = parseFloat(estimatedWorkdaysField?.value) || 0;
            const remainingWorkdays = Math.max(currentEstimatedWorkdays - totalUsedWorkdays, 0);
            const remainingWorkdaysElement = document.getElementById('remainingWorkdays');
            if (remainingWorkdaysElement) {
                remainingWorkdaysElement.textContent = `${remainingWorkdays.toFixed(1)}人日`;
            }
            
            // 5. 残金額（税抜）= 残工数（人日）* (請求単価/20*10000)
            let remainingAmount = 0;
            if (billingUnitCost > 0) {
                const dailyBillingRate = (billingUnitCost / 20) * 10000; // 万円→円変換
                remainingAmount = remainingWorkdays * dailyBillingRate;
            }
            
            const remainingAmountElement = document.getElementById('remainingAmount');
            if (remainingAmountElement) {
                remainingAmountElement.textContent = `¥${remainingAmount.toLocaleString()}`;
            }
            
            // 6. 利益率 = 残金額（税抜）/ 請求金額(税別) * 100
            let profitRate = 0;
            if (billingAmount > 0) {
                profitRate = (remainingAmount / billingAmount) * 100;
            }
            
            const profitRateElement = document.getElementById('profitRate');
            if (profitRateElement) {
                const profitClass = profitRate >= 0 ? 'text-success' : 'text-danger';
                profitRateElement.innerHTML = `<span class="${profitClass}">${profitRate.toFixed(1)}%</span>`;
            }
            
            // 7. 仕掛中金額計算（開発案件のみ）
            const wipAmountElement = document.getElementById('wipAmount');
            if (wipAmountElement && classificationSelect) {
                if (classificationSelect.value === 'development' && billingUnitCost > 0) {
                    // 開発案件：使用工数合計 × (請求単価/20*10000) + 外注費
                    const dailyBillingRate = (billingUnitCost / 20) * 10000;
                    const wipAmount = (totalUsedWorkdays * dailyBillingRate) + outsourcingCost;
                    wipAmountElement.textContent = `¥${wipAmount.toLocaleString()}`;
                } else {
                    wipAmountElement.textContent = '¥0';
                }
            }
            
            console.log('=== 自動計算完了 ===');
            
        } catch (error) {
            console.error('計算エラー:', error);
        } finally {
            isCalculating = false;
        }
    }

    // === ヘルパー関数 ===
    function setFieldValue(field, value) {
        if (field && field.value !== String(value)) {
            field.value = value;
        }
    }
    
    function setAutoCalculatedStyle(field) {
        if (field) {
            field.style.backgroundColor = '#e6f3ff';
            field.style.borderColor = '#007bff';
        }
    }
    
    function setManualEditStyle(field) {
        if (field) {
            field.style.backgroundColor = '#fff';
            field.style.borderColor = '#ced4da';
        }
    }

    // === ユーザー編集追跡機能 ===
    function setupUserModificationTracking() {
        // 見積工数フィールドの手動編集検出
        if (estimatedWorkdaysField) {
            estimatedWorkdaysField.dataset.userModified = 'false';
            
            estimatedWorkdaysField.addEventListener('focus', function() {
                this.dataset.userModified = 'true';
                setManualEditStyle(this);
            });
            
            estimatedWorkdaysField.addEventListener('input', function() {
                this.dataset.userModified = 'true';
                setManualEditStyle(this);
                setTimeout(() => {
                    if (!isCalculating) calculateValues();
                }, 100);
            });
        }
        
        // 使用可能金額フィールドの手動編集検出
        if (availableAmountField) {
            availableAmountField.dataset.userModified = 'false';
            
            availableAmountField.addEventListener('focus', function() {
                this.dataset.userModified = 'true';
                setManualEditStyle(this);
            });
            
            availableAmountField.addEventListener('input', function() {
                this.dataset.userModified = 'true';
                setManualEditStyle(this);
                setTimeout(() => {
                    if (!isCalculating) calculateValues();
                }, 100);
            });
        }
    }

    // === 計算トリガー設定 ===
    function setupCalculationTriggers() {
        const triggerFields = [
            { field: billingAmountField, name: '請求金額' },
            { field: outsourcingCostField, name: '外注費' },
            { field: usedWorkdaysField, name: '使用工数' },
            { field: newbieWorkdaysField, name: '新入社員工数' },
            { field: unitCostField, name: '原価単価' },
            { field: billingUnitCostField, name: '請求単価' }
        ];
        
        triggerFields.forEach(({ field, name }) => {
            if (field) {
                field.addEventListener('input', function() {
                    setTimeout(() => {
                        if (!isCalculating) calculateValues();
                    }, 100);
                });
                
                field.addEventListener('change', function() {
                    setTimeout(() => {
                        if (!isCalculating) calculateValues();
                    }, 100);
                });
            }
        });
        
        // チケット分類の変更時も再計算
        if (classificationSelect) {
            classificationSelect.addEventListener('change', function() {
                setTimeout(() => {
                    if (!isCalculating) calculateValues();
                }, 100);
            });
        }
    }

    // 年月変更時にも外注費を再取得
    if (yearMonthField && caseNameSelect) {
        yearMonthField.addEventListener('change', function() {
            const ticketId = caseNameSelect.value;
            if (ticketId) {
                fetchOutsourcingCost(ticketId);
            }
        });
    }

    // === 初期化実行 ===
    initializeUnifiedForm();

    // 初期計算（遅延実行）
    setTimeout(() => {
        console.log('初期自動計算を実行');
        console.log('デバッグ用コマンド: window.debugUnifiedForm.showStatus() で状態確認可能');
        calculateValues();
    }, 1000);

    console.log('=== 統合フォームJavaScript完了 ===');
});