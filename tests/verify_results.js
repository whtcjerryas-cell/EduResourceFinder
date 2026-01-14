// ========================================
// 验证批量搜索结果是否还在内存中
// ========================================

console.log('🔍 开始验证结果...\n');

// 1. 检查 window.lastBatchResults
if (window.lastBatchResults) {
    console.log('✅ 找到 window.lastBatchResults');
    console.log('   数量:', window.lastBatchResults.length);

    if (window.lastBatchResults.length === 436) {
        console.log('   ✅✅✅ 数量正确！436个结果都在！\n');

        // 显示前3个结果作为样本
        console.log('📋 前3个结果样本:');
        window.lastBatchResults.slice(0, 3).forEach((r, i) => {
            console.log(`   ${i+1}. ${r.title?.substring(0, 60)}...`);
            console.log(`      URL: ${r.url}`);
            console.log(`      分数: ${r.score}\n`);
        });

        // 立即下载备份
        console.log('💾 正在下载JSON备份...\n');
        const dataStr = JSON.stringify(window.lastBatchResults, null, 2);
        const dataBlob = new Blob([dataStr], {type: 'application/json'});
        const url = URL.createObjectURL(dataBlob);
        const link = document.createElement('a');
        link.href = url;
        const timestamp = new Date().toISOString().replace(/[:.]/g, '-').substring(0, 19);
        link.download = `iraq_results_436_${timestamp}.json`;
        link.click();
        URL.revokeObjectURL(url);

        console.log('✅✅✅ JSON备份已下载！');
        console.log('✅ 现在可以安全地重新导出Excel了！\n');

    } else {
        console.log(`   ⚠️ 数量不对，期望436，实际${window.lastBatchResults.length}\n`);
    }
} else {
    console.log('❌ window.lastBatchResults 不存在\n');
}

// 2. 检查 allResults（可能还在局部作用域）
if (typeof allResults !== 'undefined') {
    console.log('✅ 找到 allResults (局部变量)');
    console.log('   数量:', allResults.length);
} else {
    console.log('ℹ️  allResults 不在全局作用域（正常）');
}

// 3. 总结
console.log('='.repeat(80));
if (window.lastBatchResults && window.lastBatchResults.length === 436) {
    console.log('🎉 验证成功！你的436个结果完好无损！');
    console.log('📝 下一步：点击"导出批量搜索结果"按钮重新导出Excel');
} else {
    console.log('⚠️  结果可能已丢失或不完整');
    console.log('💡 建议：如果有JSON备份，可以从备份恢复');
}
console.log('='.repeat(80));
