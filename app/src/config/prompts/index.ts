/**
 * AbyssAC 提示词配置索引
 * 
 * 所有提示词都从此文件导出，方便统一管理
 * 修改对应的.ts文件即可自定义提示词
 */

export { layer1Prompt } from './layer1_nng_navigation';
export { layer2Prompt } from './layer2_memory_filter';
export { layer3Prompt } from './layer3_context_assembly';
export { 
  dmnPrompts,
  dmnQuestionOutputPrompt,
  dmnAnalysisPrompt,
  dmnReviewPrompt,
  dmnOrganizePrompt,
  dmnFormatReviewPrompt,
  userInteractionPrompt,
} from './dmn_agents';
