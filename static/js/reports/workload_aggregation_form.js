document.addEventListener('DOMContentLoaded', function() {
    // テンプレートから渡された設定を使用
    const config = window.formConfig;
    if (!config) {
        console.error('formConfigが見つかりません。テンプレートでformConfigを設定してください。');
        return;
    }

    // DOM要素の取得（設定から動的に取得）
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

    // console.log('=== DOM要素の取得状況 ===');
    // console.log('- projectSelect:', !!projectSelect, projectSelect ? projectSelect.id : 'null');
    // console.log('- caseNameSelect:', !!caseNameSelect, caseNameSelect ? caseNameSelect.id : 'null');
    // console.log('- classificationSelect:', !!classificationSelect, classificationSelect ? classificationSelect.id : 'null');
    // console.log('- projectSelectId from config:', config.projectSelectId);
    // console.log('- caseNameSelectId from config:', config.caseNameSelectId);
    // console.log('========================');

    // 計算処理中フラグ（無限ループ防止）
    let isCalculating = false;
    
    // プロジェクト選択時にチケット一覧を更新
    if (projectSelect && caseNameSelect) {
        console.log('プロジェクト選択イベントリスナーを追加します');
        
        projectSelect.addEventListener('change', function() {
            const projectId = this.value;
            // console.log('=== プロジェクト選択イベント発生 ===');
            // console.log('選択されたプロジェクトID:', projectId);
            // console.log('API URL:', config.ticketsApiUrl);
            
            // チケット選択肢をクリア
            caseNameSelect.innerHTML = '<option value="">チケット（案件）を選択してください</option>';
            
            if (projectId) {
                const apiUrl = `${config.ticketsApiUrl}?project_id=${projectId}`;
                
                // AJAX でチケット一覧を取得
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
                                data.tickets.forEach(ticket => {
                                    const option = document.createElement('option');
                                    option.value = ticket.id;
                                    option.textContent = ticket.title;
                                    option.setAttribute('data-classification', ticket.case_classification);
                                    caseNameSelect.appendChild(option);
                                });
                            } else {
                                const option = document.createElement('option');
                                option.value = '';
                                option.textContent = 'このプロジェクトにはチケットがありません';
                                caseNameSelect.appendChild(option);
                            }
                        } else {
                            console.error('チケット取得失敗:', data.error || '不明なエラー');
                            const option = document.createElement('option');
                            option.value = '';
                            option.textContent = 'チケット取得に失敗しました';
                            caseNameSelect.appendChild(option);
                        }
                    })
                    .catch(error => {
                        console.error('チケット取得エラー:', error);
                        const option = document.createElement('option');
                        option.value = '';
                        option.textContent = 'チケット取得中にエラーが発生しました';
                        caseNameSelect.appendChild(option);
                    });
            } else {
            }
        });
        
        // 初期状態でプロジェクトが選択されている場合の処理
        if (projectSelect.value) {
            // トリガーイベントを発生させる
            projectSelect.dispatchEvent(new Event('change'));
        }
        
    } else {
        console.error('=== 重要なエラー ===');
        console.error('プロジェクト選択またはチケット選択の要素が見つかりません');
        console.error('- projectSelect element:', projectSelect);
        console.error('- caseNameSelect element:', caseNameSelect);
        console.error('- config.projectSelectId:', config.projectSelectId);
        console.error('- config.caseNameSelectId:', config.caseNameSelectId);
        console.error('==================');
        
        // HTML内のselectタグを確認
        const allSelects = document.querySelectorAll('select');
        allSelects.forEach((select, index) => {
        });
    }

    // チケット選択時に外注費を自動取得
    if (caseNameSelect) {
        caseNameSelect.addEventListener('change', function() {
            const ticketId = this.value;
            const selectedOption = this.options[this.selectedIndex];
            
            if (ticketId) {
                // 外注費を取得
                fetchOutsourcingCost(ticketId);
                
                if (autoCalculateCheckbox && autoCalculateCheckbox.checked) {
                    //チケットト分類を自動設定
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

    // デバッグ用の関数をグローバルに公開
    // window.debugTickets = {
    //     checkElements: function() {
    //         console.log('=== 要素チェック ===');
    //         console.log('projectSelect:', projectSelect);
    //         console.log('caseNameSelect:', caseNameSelect);
    //         console.log('config:', config);
    //     },
    //     testTicketFetch: function(projectId) {
    //         const apiUrl = `${config.ticketsApiUrl}?project_id=${projectId}`;
    //         console.log('テスト用チケット取得:', apiUrl);
    //         fetch(apiUrl)
    //             .then(response => response.json())
    //             .then(data => console.log('テスト結果:', data))
    //             .catch(error => console.error('テストエラー:', error));
    //     },
    //     triggerProjectChange: function() {
    //         if (projectSelect && projectSelect.value) {
    //             console.log('手動でプロジェクト変更イベントをトリガー');
    //             projectSelect.dispatchEvent(new Event('change'));
    //         } else {
    //             console.log('プロジェクトが選択されていません');
    //         }
    //     }
    // };

    // 外注費取得関数
    function fetchOutsourcingCost(ticketId) {
        if (!ticketId || !outsourcingCostField) return;
        
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
                    
                    // // 詳細情報をコンソールに表示（デバッグ用）
                    // if (data.cost_details && data.cost_details.length > 0) {
                    //     console.log(`総件数: ${data.count}件, 総外注費: ¥${data.total_cost.toLocaleString()}`);
                    // } else {
                    //     console.log('このチケットには外注費の登録がありません');
                    // }
                    
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

    // 年月変更時にも外注費を再取得
    if (yearMonthField && caseNameSelect) {
        yearMonthField.addEventListener('change', function() {
            const ticketId = caseNameSelect.value;
            if (ticketId) {
                fetchOutsourcingCost(ticketId);
            }
        });
    }

    // 工数計算関数（リアルタイム用）
    function calculateWorkdays(ticketId, classification) {
        if (!ticketId) return;
        
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
    
    // 従来の工数自動取得機能（期間考慮版）
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
    
    // 自動計算機能
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
            
            // console.log('取得した値:', {
            //     billingAmount, outsourcingCost, estimatedWorkdays, 
            //     usedWorkdays, newbieWorkdays, unitCost, billingUnitCost
            // });
            
            // 1. 使用可能金額(税別) = 請求金額(税別) - 外注費（税別）
            const actualAvailableAmount = Math.max(billingAmount - outsourcingCost, 0);
            // console.log('使用可能金額計算:', billingAmount, '-', outsourcingCost, '=', actualAvailableAmount);
            
            // 使用可能金額の自動設定
            if (availableAmountField && availableAmountField.dataset.userModified !== 'true') {
                if (billingAmount > 0 || outsourcingCost > 0) {
                    // console.log('使用可能金額を自動設定:', actualAvailableAmount);
                    setFieldValue(availableAmountField, Math.round(actualAvailableAmount));
                    setAutoCalculatedStyle(availableAmountField);
                }
            }
            
            // 2. 見積工数（人日）のデフォルト = 使用可能金額(税別) / (請求単価/20*10000)
            if (estimatedWorkdaysField && estimatedWorkdaysField.dataset.userModified !== 'true') {
                // console.log('見積工数の自動計算チェック:');
                // console.log('- billingUnitCost:', billingUnitCost);
                // console.log('- actualAvailableAmount:', actualAvailableAmount);
                // console.log('- userModified:', estimatedWorkdaysField.dataset.userModified);
                
                if (billingUnitCost > 0 && actualAvailableAmount > 0) {
                    const dailyRate = (billingUnitCost / 20) * 10000; // 万円→円変換
                    const defaultEstimatedWorkdays = actualAvailableAmount / dailyRate;
                    
                    // console.log('見積工数詳細計算:');
                    // console.log('- billingUnitCost:', billingUnitCost, '万円/月');
                    // console.log('- dailyRate:', dailyRate, '円/日');
                    // console.log('- actualAvailableAmount:', actualAvailableAmount, '円');
                    // console.log('- defaultEstimatedWorkdays:', defaultEstimatedWorkdays, '人日');
                    
                    if (defaultEstimatedWorkdays > 0 && isFinite(defaultEstimatedWorkdays)) {
                        // console.log('✓ 見積工数を自動設定:', defaultEstimatedWorkdays.toFixed(1), '人日');
                        setFieldValue(estimatedWorkdaysField, defaultEstimatedWorkdays.toFixed(1));
                        setAutoCalculatedStyle(estimatedWorkdaysField);
                    } else {
                        // console.log('✗ 見積工数の計算結果が無効:', defaultEstimatedWorkdays);
                    }
                } else {
                    // console.log('✗ 見積工数計算の前提条件が不足');
                    // console.log('  - 請求単価 > 0:', billingUnitCost > 0);
                    // console.log('  - 使用可能金額 > 0:', actualAvailableAmount > 0);
                }
            } else {
                // console.log('✗ 見積工数の自動計算をスキップ（手動編集済み）');
            }
            
            // 3. 使用工数合計計算
            const totalUsedWorkdays = usedWorkdays + newbieWorkdays;
            const totalUsedWorkdaysElement = document.getElementById('totalUsedWorkdays');
            if (totalUsedWorkdaysElement) {
                totalUsedWorkdaysElement.textContent = `${totalUsedWorkdays.toFixed(1)}人日`;
            }
            
            // 4. 残工数計算（更新された見積工数を使用）
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
    
    // フィールドに値を安全に設定する関数
    function setFieldValue(field, value) {
        if (field && field.value !== String(value)) {
            field.value = value;
            // console.log(`フィールド値設定: ${field.id} = ${value}`);
        }
    }
    
    // 自動計算フィールドのスタイルを設定
    function setAutoCalculatedStyle(field) {
        if (field) {
            field.style.backgroundColor = '#e6f3ff';
            field.style.borderColor = '#007bff';
        }
    }
    
    // 手動編集フィールドのスタイルを設定
    function setManualEditStyle(field) {
        if (field) {
            field.style.backgroundColor = '#fff';
            field.style.borderColor = '#ced4da';
        }
    }
    
    // ユーザーが手動で入力した場合のフラグ設定
    function setupUserModificationTracking() {
        // 見積工数フィールドの手動編集検出
        if (estimatedWorkdaysField) {
            // 初期状態を設定
            estimatedWorkdaysField.dataset.userModified = 'false';
            
            // フォーカス時（手動編集開始）
            estimatedWorkdaysField.addEventListener('focus', function() {
                // console.log('見積工数フィールドにフォーカス - 手動編集モード開始');
                this.dataset.userModified = 'true';
                setManualEditStyle(this);
            });
            
            // 直接入力時
            estimatedWorkdaysField.addEventListener('input', function() {
                // console.log('見積工数が手動で入力されました:', this.value);
                this.dataset.userModified = 'true';
                setManualEditStyle(this);
                // 他の計算は継続
                setTimeout(() => {
                    if (!isCalculating) calculateValues();
                }, 100);
            });
        }
        
        // 使用可能金額フィールドの手動編集検出
        if (availableAmountField) {
            // 初期状態を設定
            availableAmountField.dataset.userModified = 'false';
            
            // フォーカス時（手動編集開始）
            availableAmountField.addEventListener('focus', function() {
                console.log('使用可能金額フィールドにフォーカス - 手動編集モード開始');
                this.dataset.userModified = 'true';
                setManualEditStyle(this);
            });
            
            // 直接入力時
            availableAmountField.addEventListener('input', function() {
                console.log('使用可能金額が手動で入力されました:', this.value);
                this.dataset.userModified = 'true';
                setManualEditStyle(this);
                // 他の計算は継続
                setTimeout(() => {
                    if (!isCalculating) calculateValues();
                }, 100);
            });
        }
    }
    
    // 計算トリガーフィールドのイベントリスナー設定
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
                    // console.log(`${name}が変更されました: ${this.value}`);
                    setTimeout(() => {
                        if (!isCalculating) calculateValues();
                    }, 100);
                });
                
                field.addEventListener('change', function() {
                    // console.log(`${name}が確定されました: ${this.value}`);
                    setTimeout(() => {
                        if (!isCalculating) calculateValues();
                    }, 100);
                });
            }
        });
        
        // チケット分類の変更時も再計算
        if (classificationSelect) {
            classificationSelect.addEventListener('change', function() {
                // console.log(チケットト分類変更:', this.value);
                setTimeout(() => {
                    if (!isCalculating) calculateValues();
                }, 100);
            });
        }
    }
    
    // 自動計算リセット機能（デバッグ用）
    function resetAutoCalculation() {
        console.log('自動計算をリセットします');
        
        if (estimatedWorkdaysField) {
            estimatedWorkdaysField.dataset.userModified = 'false';
            setAutoCalculatedStyle(estimatedWorkdaysField);
        }
        
        if (availableAmountField) {
            availableAmountField.dataset.userModified = 'false';
            setAutoCalculatedStyle(availableAmountField);
        }
        
        setTimeout(() => {
            if (!isCalculating) calculateValues();
        }, 100);
    }
    
    // デバッグ用コンソールコマンド
    // window.debugCalculation = {
    //     reset: resetAutoCalculation,
    //     calculate: calculateValues,
    //     showStatus: function() {
    //         console.log('=== 自動計算状態 ===');
    //         console.log('見積工数 userModified:', estimatedWorkdaysField?.dataset.userModified);
    //         console.log('使用可能金額 userModified:', availableAmountField?.dataset.userModified);
    //         console.log('現在の値:');
    //         console.log('- 請求金額:', billingAmountField?.value);
    //         console.log('- 外注費:', outsourcingCostField?.value);
    //         console.log('- 請求単価:', billingUnitCostField?.value);
    //         console.log('- 見積工数:', estimatedWorkdaysField?.value);
    //         console.log('- 使用可能金額:', availableAmountField?.value);
    //     }
    // };
    
    // 初期化
    setupUserModificationTracking();
    setupCalculationTriggers();
    
    // 初期計算（遅延実行）
    setTimeout(() => {
        console.log('初期自動計算を実行');
        console.log('デバッグ用コマンド: window.debugCalculation.showStatus() で状態確認可能');
        calculateValues();
    }, 1000);
    
    console.log('工数集計フォーム読み込み完了');
});