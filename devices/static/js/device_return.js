// static/js/device_return.js
document.addEventListener('DOMContentLoaded', function() {
    // 获取必要的元素
    const hasIssueYes = document.getElementById('has_issue_yes');
    const hasIssueNo = document.getElementById('has_issue_no');
    const issueDescriptionContainer = document.getElementById('issue_description_container');
    const returnForm = document.getElementById('returnForm');
    const issueDescriptionInput = document.getElementById('id_issue_description');  // 使用固定 ID
    const errorModal = new bootstrap.Modal(document.getElementById('errorModal'));
    const errorMessage = document.getElementById('errorMessage');

    // 调试信息：检查元素是否成功获取
    // console.log('hasIssueYes:', hasIssueYes);
    // console.log('hasIssueNo:', hasIssueNo);
    // console.log('issueDescriptionContainer:', issueDescriptionContainer);
    // console.log('returnForm:', returnForm);
    // console.log('issueDescriptionInput:', issueDescriptionInput);
    // console.log('errorModal:', errorModal);
    // console.log('errorMessage:', errorMessage);

    // 初始化显示状态
    updateIssueDescriptionVisibility();

    // 监听单选按钮变化
    hasIssueYes.addEventListener('change', updateIssueDescriptionVisibility);
    hasIssueNo.addEventListener('change', updateIssueDescriptionVisibility);

    // 更新显示状态的函数
    function updateIssueDescriptionVisibility() {
        if (hasIssueYes.checked) {
            issueDescriptionContainer.style.display = 'block';
        } else {
            issueDescriptionContainer.style.display = 'none';
        }
    }

    // 表单提交验证
    returnForm.addEventListener('submit', function(event) {
        if (hasIssueYes.checked && (!issueDescriptionInput || issueDescriptionInput.value.trim() === '')) {
            errorMessage.textContent = '请详细描述设备出现的异常情况。';
            errorModal.show();
            event.preventDefault();
        }
    });

    // 监听模态框隐藏事件
    const errorModalElement = document.getElementById('errorModal');
    errorModalElement.addEventListener('hidden.bs.modal', function () {
        if (hasIssueYes.checked && (!issueDescriptionInput || issueDescriptionInput.value.trim() === '')) {
            // 添加延迟以确保模态框完全隐藏
            setTimeout(() => {
                issueDescriptionInput.focus();
                // 添加调试信息，确认聚焦操作
                // console.log('尝试聚焦到输入框');
            }, 100);
        }
    });
});